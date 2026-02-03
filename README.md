# 图像标注工具 (ImageAnnotationTool)

一个基于PyQt5开发的多功能图像标注工具，支持多边形、边界框、线条和点等多种标注类型，适用于计算机视觉数据标注任务，助力目标检测、图像分割等算法的训练数据制备。

## 功能特性

- ✅ 多种标注类型：支持多边形(POLYGON)、边界框(BBOX)、线条(LINE)、点(POINT)等标注形式，覆盖主流计算机视觉标注场景
- ✅ 直观的标注界面：提供友好的图形界面，支持标注点的拖拽调整、实时预览，降低标注操作门槛
- ✅ 图像查看与操作：支持图像缩放、旋转等基本操作，适配不同尺寸、角度的图像标注需求
- ✅ 数据持久化：以JSON格式保存标注数据，结构规范、易于解析，确保标注数据安全可追溯
- ✅ 多语言支持：支持多种语言的文本标注，适配多语种场景下的标注需求
- ✅ 高DPI适配：自动适配不同屏幕分辨率，确保界面清晰、操作流畅，避免高分屏模糊问题

## 技术栈

- 开发语言：Python
- GUI框架：PyQt5
- UI组件库：QtUniversalToolFrameWork

## 安装说明

### 环境要求
- Python 3.6+
- Windows/Linux兼容（推荐Windows 10+、Ubuntu 20.04+）

### 安装步骤
```bash
# 克隆项目（替换<仓库地址>为实际仓库链接）
git clone <仓库地址>
cd ImageAnnotationTool

# 创建虚拟环境（可选但推荐，避免依赖冲突）
python -m venv .venv

# Windows激活虚拟环境
.venv\Scripts\activate
# Linux激活虚拟环境
# source .venv/bin/activate

# 安装依赖（国内用户可添加 -i https://pypi.tuna.tsinghua.edu.cn/simple 加速）
pip install -r requirements.txt

# 运行程序
python main.py