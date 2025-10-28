"""
learn_python - Python 学习项目
遵循最小化依赖原则
"""
from setuptools import setup, find_packages

# 读取 README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="learn_python",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Python 学习项目 - 遵循最小化依赖原则",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/learn_python",
    packages=find_packages(exclude=["tests", "docs", ".specify"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    
    # 核心依赖（遵循零依赖原则）
    install_requires=[
        # 无外部依赖 - 仅使用标准库
    ],
    
    # 可选依赖（渐进式复杂度原则）
    extras_require={
        # 开发工具
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "radon>=5.0.0",
            "pipdeptree>=2.0.0",
            "pip-audit>=2.0.0",
        ],
        # 未来扩展示例
        # "async": [
        #     "aiohttp>=3.8.0",
        # ],
        # "typing": [
        #     "typing-extensions>=4.0.0",
        # ],
        # 完整安装
        "all": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "radon>=5.0.0",
            "pipdeptree>=2.0.0",
            "pip-audit>=2.0.0",
        ],
    },
    
    # 入口点（如有需要）
    # entry_points={
    #     "console_scripts": [
    #         "learn_python=aoplib.cli:main",
    #     ],
    # },
    
    # 包含的数据文件
    include_package_data=True,
    zip_safe=False,
)

