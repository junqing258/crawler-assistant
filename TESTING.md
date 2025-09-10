# 测试指南

## 🧪 如何运行测试

本项目使用 pytest 作为测试框架，支持单元测试、集成测试和 API 测试。

### 📋 前置要求

```bash
# 1. 确保已安装开发依赖
pip install -r requirements-dev.txt

# 2. 确保已安装主要依赖
pip install -r requirements.txt

# 3. 确保环境变量已配置
cp .env.example .env  # 编辑 .env 文件
```

### 🚀 基础测试命令

```bash
# 运行所有测试
pytest

# 运行测试并显示详细信息
pytest -v

# 运行特定测试文件
pytest tests/test_basic.py -v

# 运行特定测试类
pytest tests/test_api.py::TestHealthAPI -v

# 运行特定测试方法
pytest tests/test_api.py::TestHealthAPI::test_root_endpoint -v
```

### 📊 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=. --cov-report=html --cov-report=term

# 查看覆盖率报告
open htmlcov/index.html  # macOS
# 或
xdg-open htmlcov/index.html  # Linux
```

### 🏷️ 测试标记

我们使用标记来分类测试：

```bash
# 运行单元测试
pytest -m unit

# 运行API测试
pytest -m api

# 运行集成测试
pytest -m integration

# 排除慢速测试
pytest -m "not slow"
```

### 🛠️ 调试测试

```bash
# 显示打印输出
pytest -s

# 失败时立即停止
pytest -x

# 失败时进入调试器
pytest --pdb

# 详细错误信息
pytest --tb=long
```

### 📁 测试文件结构

```
tests/
├── __init__.py
├── test_basic.py        # 基础功能测试
├── test_api.py          # API接口测试
├── test_models.py       # 数据模型测试（计划中）
├── test_services.py     # 业务服务测试（计划中）
├── test_browser.py      # 浏览器相关测试（计划中）
├── test_ai.py          # AI功能测试（计划中）
└── conftest.py         # 测试配置和fixtures
```

### 🧩 测试类型说明

#### 单元测试

- 测试单个函数或方法
- 不依赖外部服务
- 运行速度快

#### API 测试

- 测试 REST API 端点
- 验证请求响应格式
- 检查错误处理

#### 集成测试

- 测试多个组件协作
- 可能需要数据库或外部服务
- 运行时间较长

### ⚙️ 测试配置

#### pytest.ini 配置

```ini
[tool:pytest]
testpaths = tests
addopts = --strict-markers --verbose
markers =
    slow: 慢速测试
    integration: 集成测试
    unit: 单元测试
    api: API测试
```

#### conftest.py fixtures

```python
@pytest.fixture
def client():
    """测试客户端"""
    # 返回FastAPI测试客户端

@pytest.fixture
def mock_database():
    """模拟数据库"""
    # 返回测试数据库连接
```

### 🔍 测试最佳实践

1. **测试命名**：使用描述性的测试名称

   ```python
   def test_analyze_url_with_valid_input_returns_selectors():
       pass
   ```

2. **测试结构**：遵循 AAA 模式

   ```python
   def test_example():
       # Arrange - 准备测试数据
       url = "https://example.com"

       # Act - 执行被测试的操作
       result = analyze_url(url)

       # Assert - 验证结果
       assert result["success"] is True
   ```

3. **使用 fixtures**：共享测试设置

   ```python
   @pytest.fixture
   def sample_data():
       return {"key": "value"}

   def test_with_fixture(sample_data):
       assert sample_data["key"] == "value"
   ```

4. **模拟外部依赖**：使用 unittest.mock

   ```python
   from unittest.mock import patch

   @patch('app.services.openai_client')
   def test_ai_analysis(mock_openai):
       mock_openai.return_value = "mocked response"
       # 测试逻辑
   ```

### 🚨 常见问题解决

#### 依赖问题

```bash
# 错误：ModuleNotFoundError
# 解决：安装缺失的依赖
pip install missing-package

# 错误：Import error
# 解决：检查PYTHONPATH或使用相对导入
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 环境问题

```bash
# 错误：Environment variable not found
# 解决：设置测试环境变量
export TEST_DATABASE_URL=sqlite:///test.db
```

#### 数据库问题

```bash
# 错误：Database connection failed
# 解决：使用SQLite进行测试
DATABASE_URL=sqlite:///test.db pytest
```

### 📈 持续集成

#### GitHub Actions 示例

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### 📝 编写新测试

1. **创建测试文件**：以 `test_` 开头
2. **创建测试类**：以 `Test` 开头
3. **创建测试方法**：以 `test_` 开头
4. **添加适当的标记**：使用 `@pytest.mark.标记名`
5. **编写清晰的断言**：使用描述性的断言消息

### 🎯 测试目标

- [ ] 单元测试覆盖率 > 80%
- [ ] API 测试覆盖所有端点
- [ ] 集成测试覆盖关键流程
- [ ] 性能测试验证响应时间
- [ ] 安全测试检查输入验证

---

需要帮助？查看 [pytest 官方文档](https://docs.pytest.org/) 或提交 issue。
