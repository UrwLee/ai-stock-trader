#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
import os

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 项目日志目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(name: str = None) -> logger:
    """
    设置日志器

    Args:
        name: 模块名称

    Returns:
        配置好的logger对象
    """
    # 移除默认处理器
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{message}</cyan>",
        level="INFO",
        colorize=True
    )

    # 添加文件输出
    log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    logger.add(
        log_file,
        rotation="00:00",  # 每天0点切割
        retention="7 days",  # 保留7天
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG"
    )

    return logger


# 创建默认日志器
default_logger = setup_logger(__name__)


class LoggerMixin:
    """日志混入类"""

    @property
    def logger(self):
        """获取日志器"""
        return default_logger
