# Makefile for Python project

# 定义使用的 Python 解释器
PYTHON = python3

# 定义格式化工具和代码检查工具
FORMATTER = black
LINTER = flake8

# 定义要格式化和检查的目录（可以根据需要修改）
SRC_DIR = .

.PHONY: all clean format lint

# 默认目标：格式化代码并检查代码风格
all: format lint

# 清除 __pycache__ 目录和 .pyc 文件
clean:
	@echo "清除 __pycache__ 目录和 .pyc 文件..."
	find $(SRC_DIR) -type d -name "__pycache__" -exec rm -r {} +;
	find $(SRC_DIR) -type f -name "*.pyc" -delete
	@echo "清除完成。"

# 自动格式化代码
format:
	@echo "格式化代码..."
	$(FORMATTER) $(SRC_DIR)
	@echo "格式化完成。"

# 自动检查代码风格
lint:
	@echo "检查代码风格..."
	$(LINTER) $(SRC_DIR)
	@echo "代码风格检查完成。"
