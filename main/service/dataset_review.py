import traceback

from main.model.db_models import Review_result, Pending_aibom, Pending_review, Review_result
from main import db  # db is not required for queries, but is required for writes

import os
import time
import random
from werkzeug.utils import secure_filename
import csv
import xlrd
import codecs


def review_upload(user_id, dataset_review_list):
    """
    @param: user_id: 上传数据集获取使用风险的用户
    @param: dataset_review_list: 上传的数据集定位信息列表
    """
    datasets_review_result = []  # 可直接返回给用户结果的数据集列表
    datasets_pending_aibom = []  # 需用户补充AIBOM，经审核后再返回给用户的数据集列表

    for dataset_review in dataset_review_list:
        # 获取每个数据集的定位信息
        name = dataset_review.get("name", "")
        location = dataset_review.get("location", "")
        originator = dataset_review.get("originator", [])
        # 用英文逗号分割，去除左右空格，并转成hashset
        originator = set([contributor.strip() for contributor in originator.split(",")])

        # 从表review_result中获取潜在对应的已审核过的数据集
        try:
            review_result = Review_result.query.filter_by(name=name, location=location).all()
        except Exception as e:
            ret = dict()
            ret['message'] = 'fail'
            ret['notification'] = e
            return ret

        is_reviewed = False  # 该数据集是否审核过

        if name != "" and location != "" and len(originator) != 0:
            for review in review_result:
                # 获取该潜在对应的已审核过的数据集的originator
                review_originator = set([originator.strip() for originator in review.originator.split(",")])
                # 计算用户上传数据集和潜在审核过数据集的originator交集个数
                intersection = len(originator & review_originator)
                # 如果交集个数大于等于2，或用户提供的一半以上的originator重合，则认为用户上传的数据集已审核过
                if intersection >= 2 or intersection / len(originator) >= 0.5:
                    datasets_review_result.append(review)
                    is_reviewed = True
                    break

        if not is_reviewed:
            dataset_pending_aibom = pending_aibom_transfer(dataset_review, user_id)
            try:
                db.session.add(dataset_pending_aibom)
                db.session.commit()
                datasets_pending_aibom.append(dataset_pending_aibom)
            except Exception as e:
                print(e)
                db.session.rollback()

    ret = dict()
    ret['review_result_list'] = datasets_review_result
    ret['pending_aibom_list'] = datasets_pending_aibom
    ret['message'] = 'success'
    ret['notification'] = ''

    return ret


def get_pending_aibom_by_user(user_id):
    ret = dict()
    try:
        pending_aibom = Pending_aibom.query.filter_by(user_id=user_id).all()
        ret['pending_aibom_list'] = pending_aibom
        ret['message'] = 'success'
        ret['notification'] = ''
    except Exception as e:
        ret['message'] = 'fail'
        ret['notification'] = e
    return ret


def save_pending_aibom_list(pending_aibom_list):
    ret = dict()
    if len(pending_aibom_list) == 0:
        ret['message'] = 'fail'
        ret['notification'] = 'nothing to save'
        return ret

    for new_pending_aibom in pending_aibom_list:
        try:
            ori_pending_aibom = Pending_aibom.query.filter_by(id=new_pending_aibom.get('id', ''),
                                                              user_id=new_pending_aibom.get('user_id', '')).first()
        except Exception as e:
            ret['message'] = 'fail'
            ret['notification'] = e
            return ret

        if ori_pending_aibom is not None:
            ori_pending_aibom = pending_aibom_transfer(new_pending_aibom, new_pending_aibom.get('user_id', ''),
                                                       ori_pending_aibom)
            try:
                db.session.add(ori_pending_aibom)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                ret['message'] = 'fail'
                ret['notification'] = e
                return ret

    ret['message'] = 'success'
    ret['notification'] = ''

    return ret


def submit_pending_aibom_list(pending_aibom_list):
    ret = dict()
    if len(pending_aibom_list) == 0:
        ret['message'] = 'fail'
        ret['notification'] = 'nothing to submit'
        return ret

    error_pending_aibom_format = []

    for pending_aibom in pending_aibom_list:
        is_pass = format_check_aibom(pending_aibom)  # 格式检查

        if is_pass:
            pending_review = convert_aibom_to_review(pending_aibom)
            to_delete = Pending_aibom.query.filter_by(id=pending_aibom.get('id', ''),
                                                              user_id=pending_aibom.get('user_id', '')).first()
            if to_delete is None:
                ret['message'] = 'fail'
                ret['notification'] = 'pending aibom中已无该条数据，无法submit'
                return ret

            to_delete = Pending_aibom.__table__.delete().where(Pending_aibom.user_id == pending_aibom.get('user_id', '')).where(
                Pending_aibom.id == pending_aibom.get('id', ''))

            try:
                db.session.execute(to_delete)
                db.session.add(pending_review)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                ret['message'] = 'fail'
                ret['notification'] = e
                return ret
        else:
            error_pending_aibom_format.append(pending_aibom)

    if len(error_pending_aibom_format) != 0:
        ret['pending_aibom_list'] = error_pending_aibom_format
        ret['message'] = "fail"
        ret['notification'] = "AIBOM信息已提交, {}个数据集的AIBOM部分格式错误, 请修改后提交".format(len(error_pending_aibom_format))
    else:
        ret['message'] = "success"
        ret['notification'] = ""

    return ret


def remove_pending_aibom_list(user_id, pending_aibom_ids):
    to_delete = Pending_aibom.__table__.delete().where(Pending_aibom.user_id == user_id).where(
        Pending_aibom.id.in_(pending_aibom_ids))

    ret = dict()

    try:
        db.session.execute(to_delete)  # Execute this sql to change the database via session
        db.session.commit()  # Transaction commit.

        ret['message'] = 'success'
        ret['notification'] = ''

    except Exception as e:
        db.session.rollback()

        ret['message'] = 'fail'
        ret['notification'] = e

    return ret


def get_pending_review_list(user_id):
    ret = dict()
    try:
        if user_id == -1:
            pending_review = Pending_review.query.all()
        else:
            pending_review = Pending_review.query.filter_by(user_id=user_id).all()
    except Exception as e:
        ret['message'] = 'fail'
        ret['notification'] = e
        return ret

    ret['pending_review_list'] = pending_review
    ret['message'] = 'success'
    ret['notification'] = ''
    return ret


def save_pending_review_list(pending_review_list):
    ret = dict()
    for new_pending_review in pending_review_list:
        ori_pending_review = Pending_review.query.filter_by(id=new_pending_review.get('id', '')).first()
        if ori_pending_review is not None:
            ori_pending_review = pending_review_transfer(ori_pending_review, new_pending_review)
            try:
                db.session.add(ori_pending_review)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                ret['message'] = 'fail'
                ret['notification'] = e
                return ret

    ret['message'] = 'success'
    ret['notification'] = ''
    return ret


def reject_review(user_id, pending_review_ids, rejection_notes):
    ret = dict()
    pending_aibom_list = []

    for index, pending_review_id in enumerate(pending_review_ids):
        pending_review = Pending_review.query.filter_by(id=pending_review_id, user_id=user_id).first()
        if pending_review is None:
            continue

        to_delete = Pending_review.__table__.delete().where(Pending_review.id == pending_review_id).where(Pending_review.user_id == user_id)

        pending_aibom = convert_review_to_aibom(pending_review)
        pending_aibom.rejection_notes = "" if index == len(rejection_notes) else rejection_notes[index]
        try:
            db.session.add(pending_aibom)
            db.session.execute(to_delete)
            db.session.commit()
            pending_aibom_list.append(pending_aibom)
        except Exception as e:
            db.session.rollback()
            ret['message'] = 'fail'
            ret['notification'] = e
            return ret

    ret['pending_aibom_list'] = pending_aibom_list
    ret['message'] = 'success'
    ret['notification'] = ''
    return ret


def submit_pending_review_list(pending_review_list):
    ret = dict()
    if len(pending_review_list) == 0:
        ret['message'] = 'fail'
        ret['notification'] = 'nothing to submit'
        return ret

    error_pending_review_format = []

    for pending_review in pending_review_list:
        is_pass = format_check_aibom(pending_review) and format_check_review(pending_review) # 格式检查

        if is_pass:
            review_result = convert_review_to_result(pending_review)
            to_delete = Pending_review.query.filter_by(id=pending_review.get('id', ''),
                                                              user_id=pending_review.get('user_id', '')).first()
            if to_delete is None:
                continue

            to_delete = Pending_review.__table__.delete().where(Pending_review.user_id == pending_review.get('user_id', '')).where(
                Pending_review.id == pending_review.get('id', ''))

            try:
                db.session.execute(to_delete)
                db.session.add(review_result)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                ret['message'] = 'fail'
                ret['notification'] = e
                return ret
        else:
            error_pending_review_format.append(pending_review)

    if len(error_pending_review_format) != 0:
        ret['pending_review_list'] = error_pending_review_format
        ret['message'] = "fail"
        ret['notification'] = "review信息已提交, {}个数据集的AIBOM或review部分格式错误, 请修改后提交".format(len(error_pending_review_format))
    else:
        ret['message'] = "success"
        ret['notification'] = ""

    return ret


def get_review_result_list(user_id):
    ret = dict()
    try:
        if user_id == -1:
            review_result = Review_result.query.all()
        else:
            review_result = Review_result.query.filter_by(user_id=user_id).all()
    except Exception as e:
        ret['message'] = 'fail'
        ret['notification'] = e
        return ret

    ret['review_result_list'] = review_result
    ret['message'] = 'success'
    ret['notification'] = ''
    return ret


def pending_aibom_transfer(new_aibom_info, user_id, ori_aibom_info=None):
    if ori_aibom_info is None:
        dataset_pending_aibom = Pending_aibom(
            name=new_aibom_info.get("name", ""),
            location=new_aibom_info.get("location", ""),
            originator=new_aibom_info.get("originator", ""),
            license_location=new_aibom_info.get("license_location", ""),
            # concluded_license=new_aibom_info.get("concluded_license", None),
            # declared_license=new_aibom_info.get("declared_license", None),
            type=new_aibom_info.get("type", ""),
            size=new_aibom_info.get("size", ""),
            intended_use=new_aibom_info.get("intended_use", ""),
            # checksum=new_aibom_info.get("checksum", None),
            # data_collection_process=new_aibom_info.get("data_collection_process", None),
            # known_biases=new_aibom_info.get("known_biases", 0),
            # sensitive_personal_information=new_aibom_info.get("sensitive_personal_information", 0),
            # offensive_content=new_aibom_info.get("offensive_content", 0),
            user_id=user_id
        )
        return dataset_pending_aibom
    else:
        if "name" in new_aibom_info.keys():
            ori_aibom_info.name = new_aibom_info.get("name", "")
        if "location" in new_aibom_info.keys():
            ori_aibom_info.location = new_aibom_info.get("location", "")
        if "originator" in new_aibom_info.keys():
            ori_aibom_info.originator = new_aibom_info.get("originator", "")
        if "license_location" in new_aibom_info.keys():
            ori_aibom_info.license_location = new_aibom_info.get("license_location", "")
        if "concluded_license" in new_aibom_info.keys():
            ori_aibom_info.concluded_license = new_aibom_info.get("concluded_license", None)
        if "declared_license" in new_aibom_info.keys():
            ori_aibom_info.declared_license = new_aibom_info.get("declared_license", None)
        if "type" in new_aibom_info.keys():
            ori_aibom_info.type = new_aibom_info.get("type", "")
        if "size" in new_aibom_info.keys():
            ori_aibom_info.size = new_aibom_info.get("size", "")
        if "intended_use" in new_aibom_info.keys():
            ori_aibom_info.intended_use = new_aibom_info.get("intended_use", "")
        if "checksum" in new_aibom_info.keys():
            ori_aibom_info.checksum = new_aibom_info.get("checksum", None)
        if "data_collection_process" in new_aibom_info.keys():
            ori_aibom_info.data_collection_process = new_aibom_info.get("data_collection_process", None)
        if "known_biases" in new_aibom_info.keys() and new_aibom_info.get("known_biases") is not None:
            ori_aibom_info.known_biases = new_aibom_info.get("known_biases", 0)
        if "sensitive_personal_information" in new_aibom_info.keys() and new_aibom_info.get("sensitive_personal_information") is not None:
            ori_aibom_info.sensitive_personal_information = new_aibom_info.get("sensitive_personal_information", 0)
        if "offensive_content" in new_aibom_info.keys() and new_aibom_info.get("offensive_content") is not None:
            ori_aibom_info.offensive_content = new_aibom_info.get("offensive_content", 0)
        return ori_aibom_info


def pending_review_transfer(ori_pending_review, new_pending_review):
    ori_pending_review.name = new_pending_review.get("name", "")
    ori_pending_review.location = new_pending_review.get("location", "")
    ori_pending_review.originator = new_pending_review.get("originator", "")
    ori_pending_review.license_location = new_pending_review.get("license_location", "")
    ori_pending_review.concluded_license = new_pending_review.get("concluded_license", None)
    ori_pending_review.declared_license = new_pending_review.get("declared_license", None)
    ori_pending_review.type = new_pending_review.get("type", "")
    ori_pending_review.size = new_pending_review.get("size", "")
    ori_pending_review.intended_use = new_pending_review.get("intended_use", "")
    ori_pending_review.checksum = new_pending_review.get("checksum", None)
    ori_pending_review.data_collection_process = new_pending_review.get("data_collection_process", None)
    ori_pending_review.known_biases = new_pending_review.get("known_biases", "")
    ori_pending_review.sensitive_personal_information = new_pending_review.get("sensitive_personal_information", None)
    ori_pending_review.offensive_content = new_pending_review.get("offensive_content", None)

    # ori_pending_review.user_id = new_pending_review.get("user_id", "")

    ori_pending_review.review_result_initial = new_pending_review.get("review_result_initial", "")
    ori_pending_review.is_dataset_commercially_used_initial = new_pending_review.get("is_dataset_commercially_used_initial", 0)
    ori_pending_review.is_dataset_commercially_distributed_initial = new_pending_review.get("is_dataset_commercially_distributed_initial", 0)
    ori_pending_review.is_product_commercially_published_initial = new_pending_review.get("is_product_commercially_published_initial", 0)
    ori_pending_review.right_initial = new_pending_review.get("right_initial", None)
    ori_pending_review.obligation_initial = new_pending_review.get("obligation_initial", None)
    ori_pending_review.limitation_initial = new_pending_review.get("limitation_initial", None)
    ori_pending_review.notes_initial = new_pending_review.get("notes_initial", None)

    return ori_pending_review


def convert_aibom_to_review(pending_aibom):
    pending_review = Pending_review(
        name=pending_aibom.get("name", ""),
        location=pending_aibom.get("location", ""),
        originator=pending_aibom.get("originator", ""),
        license_location=pending_aibom.get("license_location", ""),
        concluded_license=pending_aibom.get("concluded_license", None),
        declared_license=pending_aibom.get("declared_license", None),
        type=pending_aibom.get("type", ""),
        size=pending_aibom.get("size", ""),
        intended_use=pending_aibom.get("intended_use", None),
        checksum=pending_aibom.get("checksum", ""),
        data_collection_process=pending_aibom.get("data_collection_process", None),
        known_biases=pending_aibom.get("known_biases", 0),
        sensitive_personal_information=pending_aibom.get("sensitive_personal_information", 0),
        offensive_content=pending_aibom.get("offensive_content", 0),
        user_id=pending_aibom.get('user_id', ""),
        review_result_initial="",
        is_dataset_commercially_used_initial=0,
        is_dataset_commercially_distributed_initial=0,
        is_product_commercially_published_initial=0
    )

    # if "concluded_license" in pending_aibom.keys():
    #     pending_review.concluded_license = pending_aibom.get("concluded_license", None)
    # if "declared_license" in pending_aibom.keys():
    #     pending_review.declared_license = pending_aibom.get("declared_license", None)
    # if "checksum" in pending_aibom.keys():
    #     pending_review.checksum = pending_aibom.get("checksum", None),
    # if "data_collection_process" in pending_aibom.keys():
    #     pending_review.data_collection_process = pending_aibom.get("data_collection_process", None),
    # if "known_biases" in pending_aibom.keys() and pending_aibom.get("known_biases") is not None:
    #     flag = pending_aibom.get("known_biases", 0)
    #     # num = 1 if flag else 0
    #     pending_review.known_biases = flag,
    #     print(type(pending_review.known_biases))
    #     print(pending_review.known_biases)
    # if "sensitive_personal_information" in pending_aibom.keys() and pending_aibom.get(
    #         "sensitive_personal_information") is not None:
    #     flag = pending_aibom.get("sensitive_personal_information", 0)
    #     pending_review.sensitive_personal_information = 1 if flag else 0,
    # if "offensive_content" in pending_aibom.keys() and pending_aibom.get("offensive_content") is not None:
    #     flag = pending_aibom.get("offensive_content", 0)
    #     pending_review.offensive_content = 1 if flag else 0,

    return pending_review


def convert_review_to_aibom(pending_review):
    pending_aibom = Pending_aibom(
        name=pending_review.name,
        location=pending_review.location,
        originator=pending_review.originator,
        license_location=pending_review.license_location,
        concluded_license=pending_review.concluded_license,
        declared_license=pending_review.declared_license,
        type=pending_review.type,
        size=pending_review.size,
        intended_use=pending_review.intended_use,
        checksum=pending_review.checksum,
        data_collection_process=pending_review.data_collection_process,
        known_biases=pending_review.known_biases,
        sensitive_personal_information=pending_review.sensitive_personal_information,
        offensive_content=pending_review.offensive_content,

        user_id=pending_review.user_id,
    )

    return pending_aibom


def convert_review_to_result(pending_review):
    review_result = Review_result(
        name=pending_review.get("name", ""),
        location=pending_review.get("location", ""),
        originator=pending_review.get("originator", ""),
        license_location=pending_review.get("license_location", ""),
        concluded_license=pending_review.get("concluded_license", None),
        declared_license=pending_review.get("declared_license", None),
        type=pending_review.get("type", ""),
        size=pending_review.get("size", ""),
        intended_use=pending_review.get("intended_use", ""),
        checksum=pending_review.get("checksum", None),
        data_collection_process=pending_review.get("data_collection_process", None),
        known_biases=pending_review.get("known_biases", None),
        sensitive_personal_information=pending_review.get("sensitive_personal_information", None),
        offensive_content=pending_review.get("offensive_content", None),

        user_id=pending_review.get("user_id", ""),

        review_result_initial=pending_review.get("review_result_initial", ""),
        is_dataset_commercially_used_initial=pending_review.get("is_dataset_commercially_used_initial", 0),
        is_dataset_commercially_distributed_initial=pending_review.get("is_dataset_commercially_distributed_initial", 0),
        is_product_commercially_published_initial=pending_review.get("is_product_commercially_published_initial", 0),
        right_initial=pending_review.get("right_initial", None),
        obligation_initial=pending_review.get("obligation_initial", None),
        limitation_initial=pending_review.get("limitation_initial", None),
        notes_initial=pending_review.get("notes_initial", None),

        review_result_final="",
        is_dataset_commercially_used_final=0,
        is_dataset_commercially_distributed_final=0,
        is_product_commercially_published_final=0,
        right_final="",
        obligation_final="",
        limitation_final="",
        notes_final="",
    )

    return review_result


def format_check_aibom(pending_aibom):
    keys = {"name", "location", "originator", "license_location", "type", "size", "intended_use", "user_id"}
    for key in keys:
        if key not in pending_aibom.keys() or len(str(pending_aibom[key])) == 0:
            return False
    if "concluded_license" not in pending_aibom.keys() and "declared_license" not in pending_aibom.keys():
        return False
    if pending_aibom['concluded_license'] is None and pending_aibom['declared_license'] is None:
        return False
    if pending_aibom['concluded_license'] is not None and len(pending_aibom['concluded_license']) != 0:
        return True
    if pending_aibom['declared_license'] is not None and len(pending_aibom['declared_license']) != 0:
        return True

    return True


def format_check_review(pending_review):
    keys = {"review_result_initial", "is_dataset_commercially_used_initial", "is_dataset_commercially_distributed_initial", "is_product_commercially_published_initial"}
    for key in keys:
        if key not in pending_review.keys() or len(str(pending_review[key])) == 0:
            return False
    return True


def file_suffix_check(cur_file):
    if secure_filename(cur_file.filename).rsplit('.', 1)[1] == "csv" or secure_filename(cur_file.filename).rsplit('.', 1)[1] == "xlsx":
        return True
    return False


def file_save(user_id, cur_file):
    try:
        file_name = str(user_id) + "_" + str(int(time.time())) + "_" + str(random.randint(0, 2147483647)) + ".csv"

        # The absolute address of the target to save
        root_path = os.getcwd()  # The absolute path of the current project
        rel_path = "/static" + "/upload_by_user/"  # Relative path to the folder
        abs_path = root_path + rel_path  # The absolute path to the img

        if not os.path.exists(abs_path):
            os.makedirs(abs_path)

        if secure_filename(cur_file.filename).rsplit('.', 1)[1] == "csv":
            cur_file.save(abs_path + file_name)
        else:
            xlsx_to_csv(cur_file, abs_path + file_name)
        return True, abs_path + file_name
    except Exception as e:
        return False, e


def xlsx_to_csv(cur_file, file_path):
    xlsx_path = file_path.rsplit(".")[0] + ".xlsx"
    cur_file.save(xlsx_path)
    workbook = xlrd.open_workbook(xlsx_path)
    table = workbook.sheet_by_index(0)
    with codecs.open(file_path, 'w', encoding='utf-8') as f:
        write = csv.writer(f)
        for row_num in range(table.nrows):
            row_value = table.row_values(row_num)
            for i in range(len(row_value)):
                if isinstance(row_value[i], float) and abs(int(row_value[i]) - row_value[i]) < 0.00001:
                    row_value[i] = int(row_value[i])
            write.writerow(row_value)


def file_convert(user_id, cur_file):
    ret = dict()
    if cur_file is None:
        ret['message'] = 'fail'
        ret['notification'] = '文件未正确上传！'
        return ret

    if not file_suffix_check(cur_file):
        ret['message'] = 'fail'
        ret['notification'] = '文件后缀不匹配，请上传csv或xlsx格式的文件！'
        return ret

    is_success, msg = file_save(user_id, cur_file)
    if not is_success:
        ret['message'] = 'fail'
        ret['notification'] = msg
        return ret

    dataset_review_list = []
    cur_file = csv.reader(open(msg))
    cnt = 0
    for line in cur_file:
        if cnt == 0:
            cnt += 1
            continue
        dataset = dict()
        dataset['name'] = str(line[0])
        dataset['location'] = str(line[1])
        dataset['originator'] = str(line[2])
        dataset_review_list.append(dataset)

    ret['message'] = 'success'
    ret['notification'] = dataset_review_list
    return ret


def review_result_download(user_id, review_result_list):
    ret = dict()

    file_name = str(user_id) + "_" + str(int(time.time())) + "_" + str(random.randint(0, 2147483647)) + ".csv"
    # The absolute address of the target to save
    root_path = os.getcwd()  # The absolute path of the current project
    rel_path = "/static" + "/download_by_user/"  # Relative path to the folder
    abs_path = root_path + rel_path  # The absolute path to the img

    try:
        if not os.path.exists(abs_path):
            os.makedirs(abs_path)

        with open("." + rel_path + file_name, "w") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["name", "location", "originator", "license_location", "concluded_license", "declared_license",
                             "type", "size", "intended_use", "checksum", "data_collection_process", "known_biases",
                             "sensitive_personal_information", "offensive_content", "review_result_initial",
                             "is_dataset_commercially_used_initial", "is_dataset_commercially_distributed_initial",
                             "is_product_commercially_published_initial", "right_initial",
                             "obligation_initial", "limitation_initial", "notes_initial"])
            for review_result in review_result_list:
                writer.writerow([review_result.name, review_result.location, review_result.originator, review_result.license_location,
                                review_result.concluded_license, review_result.declared_license, review_result.type, review_result.size,
                                review_result.intended_use, review_result.checksum, review_result.data_collection_process,
                                review_result.known_biases, review_result.sensitive_personal_information,
                                review_result.offensive_content, review_result.review_result_initial,
                                review_result.is_dataset_commercially_used_initial, review_result.is_dataset_commercially_distributed_initial,
                                review_result.is_product_commercially_published_initial, review_result.right_initial,
                                review_result.obligation_initial, review_result.limitation_initial, review_result.notes_initial])
    except Exception as e:
        ret['message'] = 'fail'
        ret['notification'] = e
        return ret

    ret['message'] = 'success'
    ret['download_path'] = abs_path
    ret['file_name'] = file_name
    return ret





















