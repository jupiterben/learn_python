# learn_python

Python 学习项目 - 遵循**最小化依赖**和**标准库优先**原则的实践示例。

## 项目哲学

本项目遵循 **Python 库最小化准则**，详见 [项目宪章](.specify/memory/constitution.md)。

### 五大核心原则

1. **标准库优先** - 优先使用 Python 标准库
2. **零依赖目标** - 核心功能无外部依赖
3. **依赖审计** - 严格评估每个外部依赖
4. **API 简洁性** - 保持接口简洁清晰（< 20 个公开 API）
5. **渐进式复杂度** - 按需选择功能层级

## 安装

### 核心功能（零依赖）
```bash
pip install -e .
```

### 开发工具
```bash
pip install -e ".[dev]"
```

### 所有功能
```bash
pip install -e ".[all]"
```

## 快速开始

```python
# 使用标准库实现的装饰器示例
from aoplib.stage import simple_decorator, timer

@timer
def my_function():
    # 你的代码
    pass
```

## 项目结构

```
learn_python/
├── aoplib/              # 核心库（零外部依赖）
│   └── stage.py         # 装饰器示例
├── sample/              # 示例代码
├── test/                # 测试
├── .specify/            # 项目治理
│   ├── memory/
│   │   └── constitution.md      # 项目宪章
│   └── templates/               # 工作模板
│       ├── plan-template.md
│       ├── spec-template.md
│       ├── tasks-template.md
│       └── commands/
└── docs/                # 文档
    └── dependencies.md  # 依赖审计记录
```

## 开发指南

### 添加新功能前必读

1. 阅读 [项目宪章](.specify/memory/constitution.md)
2. 评估是否可用标准库实现
3. 如需外部依赖，参考 [依赖审计流程](docs/dependencies.md)
4. 使用 [需求规格模板](.specify/templates/spec-template.md)
5. 使用 [实施计划模板](.specify/templates/plan-template.md)

### 测试

```bash
pytest --cov=aoplib tests/
```

### 代码质量

```bash
# 格式化
black .

# 类型检查
mypy aoplib/

# 复杂度分析
radon cc aoplib/ -a

# 依赖树
pipdeptree
```

## 依赖管理

查看 [docs/dependencies.md](docs/dependencies.md) 了解所有依赖的选择理由和审计记录。

**当前状态**:
- 核心依赖: 0
- 可选依赖: 0
- 开发依赖: 3 (pytest, black, mypy)

## 贡献指南

1. Fork 本仓库
2. 创建功能分支: `git checkout -b feature/your-feature`
3. **确保符合宪章原则**（见合规性检查清单）
4. 提交 PR 并引用相关宪章原则
5. 等待 Code Review

**PR 必须包含**:
- [ ] 宪章合规性说明
- [ ] 单元测试（覆盖率 > 80%）
- [ ] 文档更新
- [ ] 依赖审计（如有新依赖）

## 许可证

MIT License

## 相关资源

- [项目宪章](.specify/memory/constitution.md) - 治理文档
- [依赖审计](docs/dependencies.md) - 依赖选择记录
- [Python 标准库文档](https://docs.python.org/3/library/) - 优先参考

