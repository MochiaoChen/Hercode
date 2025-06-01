
# 🌸 HerCode Interpreter（温柔语言解释器）

> A warm, beginner-friendly interpreter for HerCode, a soft and poetic pseudo-language for coding encouragement.
>  
> 一个温柔、鼓励式的编程语言解释器，适合编程初学者，特别为 HerCode 设计，充满仪式感与温情。

---

## 📦 项目简介 | Project Introduction

HerCode 是一种“仪式感语言”，它用 `say` 表达温柔、用 `function` 包裹想法，以 `start:` 开始每段代码旅程。  
HerCode Interpreter 则是一个用 Python 编写的解释器，可以运行 `.txt` 格式的 HerCode 源文件。

HerCode is a pseudo-language where code feels like a diary entry. It uses `say` to express warmth, `function` to wrap ideas, and `start:` to begin each journey. This interpreter allows you to execute HerCode `.txt` files.

---

## 🚀 如何运行 | How to Run

### 📁 1. 准备 HerCode 文件 | Prepare a HerCode File

创建一个 `.txt` 文件，如 `hello_world.txt`，示例如下：

```hercode
function you_can_do_this:
    say "Hello! Her World L"
    say "编程很美，也属于你！"
end

start:
    you_can_do_this
end
```

---

### 🖥️ 2. 运行解释器 | Run the Interpreter

确保你已经安装 Python 3，并在同目录下保存了解释器脚本（`hercode_runner.py`）和 `.txt` 文件。

```bash
python hercode_runner.py hello_world
```

会自动读取 `hello_world.txt` 并执行 HerCode 程序。

---

## 🧠 示例输出 | Example Output

```text
Hello! Her World L
编程很美，也属于你！
```

---

## 📂 文件结构建议 | Suggested File Structure

```
your_project_folder/
│
├── hercode_runner.py         # HerCode解释器
├── hello_world.txt           # HerCode 程序示例
└── README.md                 # 项目说明文档
```

---

## ✨ 特性 | Features

- ✅ 支持 HerCode 自定义函数
- ✅ 语法温柔友好，适合初学者
- ✅ CLI 命令行运行支持（CIL）
- ✅ 中英文兼容输出
- 🚧（计划中）支持 say with variable、条件判断、嵌套调用等更多语法扩展

---

## 📜 License

MIT License | 开源自由使用

---

> 🌷 每一行代码，都是对世界的温柔表达  
> Every line of code is a gentle note to the world.
