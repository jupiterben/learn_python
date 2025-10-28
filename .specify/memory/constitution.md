<!--
Sync Impact Report:
- Version: INITIAL → 1.0.0
- Modified principles: N/A (初始版本)
- Added sections: 全部核心原则 (5项)
- Removed sections: N/A
- Templates status:
  ✅ plan-template.md (已创建)
  ✅ spec-template.md (已创建)
  ✅ tasks-template.md (已创建)
  ✅ commands/constitution.md (已创建)
- Follow-up TODOs: 无
-->

# learn_python 项目宪章

**版本**: 1.0.0  
**批准日期**: 2025-10-28  
**最后修订**: 2025-10-28

---

## 项目使命

为 Python 开发者提供学习资源和最佳实践示例，强调**最小化依赖**和**标准库优先**的开发哲学，培养构建轻量、可维护、可部署的 Python 库的能力。

---

## 核心原则

### 原则 1：标准库优先 (Standard Library First)

**规则**：
- MUST 优先使用 Python 标准库解决问题
- MUST 在引入外部依赖前评估标准库替代方案
- MUST 在文档中说明为何标准库无法满足需求时才引入外部依赖

**理由**：标准库随 Python 发行，无需额外安装，保证跨平台兼容性和长期稳定性，减少供应链安全风险。

### 原则 2：零依赖目标 (Zero Dependency Goal)

**规则**：
- MUST 将核心功能设计为零外部依赖
- MAY 使用可选依赖（extras）扩展高级特性
- MUST 在 `requirements.txt` 和 `setup.py` 中明确区分核心依赖与可选依赖
- MUST 为可选功能提供优雅降级或明确错误提示

**理由**：零依赖降低安装复杂度、提升安全性、减少版本冲突，使库在资源受限环境（如嵌入式、Lambda）中可用。

### 原则 3：依赖审计 (Dependency Audit)

**规则**：
- MUST 对每个新依赖进行评估：
  - 维护活跃度（最近 6 个月有更新）
  - 社区规模（GitHub stars > 100 或 PyPI 下载量 > 10k/月）
  - 许可证兼容性（MIT/Apache/BSD 优先）
  - 传递依赖数量（prefer < 5）
- MUST 在 `docs/dependencies.md` 记录依赖选择理由
- MUST 每季度审查依赖必要性，移除未使用依赖

**理由**：防止依赖膨胀、供应链攻击和许可证冲突，保持项目长期健康。

### 原则 4：API 简洁性 (API Simplicity)

**规则**：
- MUST 遵循"少即是多"：公开 API 函数 < 20 个
- MUST 每个模块职责单一，避免"瑞士军刀"设计
- SHOULD 提供简单默认值，高级配置通过可选参数暴露
- MUST 避免隐式行为和"魔法"，优先显式清晰

**理由**：简洁 API 降低学习曲线，减少误用，提高代码可预测性和测试覆盖率。

### 原则 5：渐进式复杂度 (Progressive Complexity)

**规则**：
- MUST 设计三层架构：
  1. **核心层**：零依赖，实现基础功能
  2. **扩展层**：可选依赖，增强特性（如异步、类型检查）
  3. **集成层**：第三方框架适配器（如 Django、FastAPI）
- MUST 在 `setup.py` 中定义清晰的 extras 分组：
  ```python
  extras_require={
      'dev': ['pytest', 'black'],
      'async': ['aiohttp'],
      'all': ['pytest', 'black', 'aiohttp']
  }
  ```
- MUST 保证核心层独立可用

**理由**：让用户按需选择复杂度，初学者使用简单版本，高级用户扩展功能，避免强制安装不需要的依赖。

---

## 治理机制

### 修订流程

1. **提议**：通过 Issue 提出原则修改，说明动机和影响范围
2. **评审**：维护者评估对现有代码和依赖的影响
3. **投票**：需 2/3 维护者同意
4. **实施**：更新宪章，同步更新所有模板和文档

### 版本控制

- **MAJOR (x.0.0)**：删除/重新定义原则，破坏性变更
- **MINOR (0.x.0)**：新增原则或重大扩展
- **PATCH (0.0.x)**：文字澄清、示例补充

### 合规性检查

- **代码审查**：PR 必须引用宪章相关原则
- **依赖审计**：每季度运行 `pip list --outdated` 和 `pipdeptree`
- **原则验证**：每个新模块需附 `COMPLIANCE.md` 说明如何遵守各原则

---

## 强制执行

违反宪章的代码将被拒绝合并，除非：
1. 在 PR 中明确说明例外理由
2. 获得至少 1 位资深维护者批准
3. 在代码中添加 `# CONSTITUTION_EXCEPTION: <原则名> - <理由>` 注释

---

## 附录：工具推荐

**依赖分析**：
- `pipdeptree`：查看依赖树
- `pip-audit`：安全漏洞扫描
- `deptry`：未使用依赖检测

**代码简化**：
- `radon`：复杂度分析
- `vulture`：死代码检测

**文档**：
- 使用 `pdoc` 生成零依赖文档（替代 Sphinx）

---

**END OF CONSTITUTION**
