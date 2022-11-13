from main import db


# class Pending_aibom(db.Model):
#     _tablename_ = 'pending_aibom'
#
#     id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True)
#     dataset_name = db.Column(db.String(255))
#     homepage = db.Column(db.String(255))
#     copyright = db.Column(db.String(255))
#     contributor = db.Column(db.String(255))
#     license = db.Column(db.JSON)
#     right = db.Column(db.JSON)
#     badge = db.Column(db.JSON)
#     review = db.Column(db.JSON)
#     comment = db.Column(db.String(255))
#     userid = db.Column(db.Integer)

class Pending_aibom(db.Model):
    _tablename_ = 'pending_aibom'

    id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True)
    # 数据集AIBOM属性
    name = db.Column(db.String(255))  # 数据集名称
    location = db.Column(db.String(255))  # 数据集官网
    originator = db.Column(db.String(255))  # 贡献者
    license_location = db.Column(db.String(255))  # 许可地址
    concluded_license = db.Column(db.String(255))  # SPDX License List中的许可
    declared_license = db.Column(db.String(255))  # 自定义许可
    type = db.Column(db.String(255))  # 数据集格式，例如图片、音频、视频等
    size = db.Column(db.String(255))  # 数据集大小
    intended_use = db.Column(db.String(255))  # 使用目的
    checksum = db.Column(db.String(255))  # 验证
    data_collection_process = db.Column(db.String(255))  # 数据收集过程
    known_biases = db.Column(db.Boolean)  # 是否有已知偏见
    sensitive_personal_information = db.Column(db.Boolean)  # 是否有个人敏感信息
    offensive_content = db.Column(db.Boolean)  # 是否有冒犯内容
    # 上传用户信息
    user_id = db.Column(db.Integer)  # 待补充该AIBOM的用户
    # 驳回备注
    rejection_notes = db.Column(db.String(255))  # 若该数据集AIBOM提交后被驳回，可在此备注


# class Pending_review(db.Model):
#     _tablename_ = 'pending_review'
#
#     id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True)
#     dataset_name = db.Column(db.String(255))
#     homepage = db.Column(db.String(255))
#     copyright = db.Column(db.String(255))
#     contributor = db.Column(db.String(255))
#     license = db.Column(db.JSON)
#     right = db.Column(db.JSON)
#     badge = db.Column(db.JSON)
#     review = db.Column(db.JSON)
#     comment = db.Column(db.String(255))
#     userid = db.Column(db.Integer)

class Pending_review(db.Model):
    _tablename_ = 'pending_review'

    id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True)
    # 数据集AIBOM属性
    name = db.Column(db.String(255))  # 数据集名称
    location = db.Column(db.String(255))  # 数据集官网
    originator = db.Column(db.String(255))  # 贡献者
    license_location = db.Column(db.String(255))  # 许可地址
    concluded_license = db.Column(db.String(255))  # SPDX License List中的许可
    declared_license = db.Column(db.String(255))  # 自定义许可
    type = db.Column(db.String(255))  # 数据集格式，例如图片、音频、视频等
    size = db.Column(db.String(255))  # 数据集大小
    intended_use = db.Column(db.String(255))  # 使用目的
    checksum = db.Column(db.String(255))  # 验证
    data_collection_process = db.Column(db.String(255))  # 数据收集过程
    known_biases = db.Column(db.Boolean)  # 是否有已知偏见
    sensitive_personal_information = db.Column(db.Boolean)  # 是否有个人敏感信息
    offensive_content = db.Column(db.Boolean)  # 是否有冒犯内容
    # 上传用户信息
    user_id = db.Column(db.Integer)  # 待补充该AIBOM的用户
    # 初步review意见
    review_result_initial = db.Column(db.String(255))  # 初步review结论
    is_dataset_commercially_used_initial = db.Column(db.Boolean)  # 数据集是否可商业使用
    is_dataset_commercially_distributed_initial = db.Column(db.Boolean)  # 数据集是否可商业分发
    is_product_commercially_published_initial = db.Column(db.Boolean)  # 数据集是否可集成到产品发布
    right_initial = db.Column(db.String(255))  # 初步权利分析
    obligation_initial = db.Column(db.String(255))  # 初步责任分析
    limitation_initial = db.Column(db.String(255))  # 初步限制分析
    notes_initial = db.Column(db.String(255))  # 初步review的备注


# class Review_result(db.Model):
#     _tablename_ = 'dataset_review'
#
#     id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True)
#     dataset_name = db.Column(db.String(255))
#     homepage = db.Column(db.String(255))
#     copyright = db.Column(db.String(255))
#     contributor = db.Column(db.String(255))
#     license = db.Column(db.JSON)
#     right = db.Column(db.JSON)
#     badge = db.Column(db.JSON)
#     review = db.Column(db.JSON)
#     comment = db.Column(db.String(255))


class Review_result(db.Model):
    _tablename_ = 'dataset_review'

    id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True)
    # 数据集AIBOM属性
    name = db.Column(db.String(255))  # 数据集名称
    location = db.Column(db.String(255))  # 数据集官网
    originator = db.Column(db.String(255))  # 贡献者
    license_location = db.Column(db.String(255))  # 许可地址
    concluded_license = db.Column(db.String(255))  # SPDX License List中的许可
    declared_license = db.Column(db.String(255))  # 自定义许可
    type = db.Column(db.String(255))  # 数据集格式，例如图片、音频、视频等
    size = db.Column(db.String(255))  # 数据集大小
    intended_use = db.Column(db.String(255))  # 使用目的
    checksum = db.Column(db.String(255))  # 验证
    data_collection_process = db.Column(db.String(255))  # 数据收集过程
    known_biases = db.Column(db.Boolean)  # 是否有已知偏见
    sensitive_personal_information = db.Column(db.Boolean)  # 是否有个人敏感信息
    offensive_content = db.Column(db.Boolean)  # 是否有冒犯内容
    # 上传用户信息
    user_id = db.Column(db.Integer)  # 待补充该AIBOM的用户
    # 初步review意见
    review_result_initial = db.Column(db.String(255))  # 初步review结论
    is_dataset_commercially_used_initial = db.Column(db.Boolean)  # 数据集是否可商业使用
    is_dataset_commercially_distributed_initial = db.Column(db.Boolean)  # 数据集是否可商业分发
    is_product_commercially_published_initial = db.Column(db.Boolean)  # 数据集是否可集成到产品发布
    right_initial = db.Column(db.String(255))  # 初步权利分析
    obligation_initial = db.Column(db.String(255))  # 初步责任分析
    limitation_initial = db.Column(db.String(255))  # 初步限制分析
    notes_initial = db.Column(db.String(255))  # 初步review的备注
    # 最终review意见
    review_result_final = db.Column(db.String(255))  # 最终review结论
    is_dataset_commercially_used_final = db.Column(db.Boolean)  # 数据集是否可商业使用
    is_dataset_commercially_distributed_final = db.Column(db.Boolean)  # 数据集是否可商业分发
    is_product_commercially_published_final = db.Column(db.Boolean)  # 数据集是否可集成到产品发布
    right_final = db.Column(db.String(255))  # 最终权利分析
    obligation_final = db.Column(db.String(255))  # 最终责任分析
    limitation_final = db.Column(db.String(255))  # 最终限制分析
    notes_final = db.Column(db.String(255))  # 最终review的备注


class Users(db.Model):
    _tablename_ = 'users'

    id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True)
    account = db.Column(db.String(255))
    password = db.Column(db.String(255))
    verification = db.Column(db.String(255))
