from configs.base_config import BaseConfig

class Configuration(BaseConfig):
    DEBUG = True


    POSTGRES = {
        'user': 'root',
        'pw': 'S.yogaraj#29',
        'db': 'aarganic',
        'host': '127.0.0.1:8000',
        'port': '3306',
        'ssl': ''
        }

    DB_URI = 'mysql+pymysql://root:S.yogaraj#29@localhost/aarganic' 

    #DB_URI = 'mysql+pymysql://aarganic:Aarganic_13@mysql.selfmade.ninja/aarganic_1' 

    # SQLALCHEMY_DATABASE_URL = 'mysql+pymysql://root:@localhost/hotelerp'   