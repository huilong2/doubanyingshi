import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("AccountManager")

def chagyong_load_config(quan_shujuwenjianjia):
    """加载配置文件，返回config字典"""
    config_data = {}
    try:
        # 优先使用配置系统
        try:
            from config import config as program_config
            config_path = program_config.get_config_path()
        except ImportError:
            # 如果配置系统不可用，使用传入的路径
            config_path = Path(quan_shujuwenjianjia) / 'peizhi.json'
        
        # 确保配置文件目录存在
        config_path.parent.mkdir(exist_ok=True)
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                logger.info(f"已加载配置: {config_data}")
        else:
            logger.warning("配置文件不存在")
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}")
    return config_data

def chagyong_save_config(quan_shujuwenjianjia, config):
    """保存配置文件，将config字典写入peizhi.json"""
    try:
        # 优先使用配置系统
        try:
            from config import config as program_config
            config_path = program_config.get_config_path()
        except ImportError:
            # 如果配置系统不可用，使用传入的路径
            config_path = Path(quan_shujuwenjianjia) / 'peizhi.json'
        
        # 确保配置文件目录存在
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存: {config}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False

