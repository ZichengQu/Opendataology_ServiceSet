from flask_restplus import Namespace

user_dataset_review_ns = Namespace("普通用户端 Dataset Review API",
                                   description="All functions for dataset review.")

auth_dataset_review_ns = Namespace("后台审核者 Dataset Review API",
                                   description="All functions for dataset review.")
