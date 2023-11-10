# TIS (Text Image Synthesizer) 文本图像合成器

TIS (Text Image Synthesizer)是一个文本图像合成器，用于将文本信息合成图像数据集给OCR检测识别模型预训练。

## 功能特点

1. 支持多种模式，包括以下类型：
    - 弧形文本 (arctext)
    - 银行卡 (bankcard)
    - 银行流水 (bankflow)
    - 书籍 (book)
    - 商务名片 (businesscard)
    - 优惠券 (coupon)
    - 快递单 (express)
    - 财务报表 (financial_statement)
    - 表单 (form)
    - 身份证 (idcard)
    - 布局 (layout)
    - 杂志 (magazine)
    - 菜单 (menu)
    - 报纸 (newspaper)
    - 无线表格 (noline)
    - 护照 (passport)
    - 收据 (receipt)
    - 会员卡 (vipcard)
    - ~~- 运单 (waybill)~~

2. 支持的语言类型
    - 中文: zh_CN
    - 英语: en
    - 印尼语: id
    - 菲律宾语: fil_PH
    - 荷兰语: nl_be
    - 捷克语: cs
    - 希腊语: el_GR
    - 孟加拉语: bn
    - 尼泊尔语: ne
    - 僧伽罗语: si
    - 柬埔寨语: km
    - 老挝语: lo_LA
    - 马来语: ms_MY

## 安装

1. 克隆项目到本地：

```bash
git clone https://github.com/arry-lee/TIS.git
```

安装依赖：

```bash
cd TIS
pip install -r requirements.txt
```

## 使用说明

设置参数并运行 TIS：

```bash
python tis -m MODE -b BATCH -l LANG
参数说明
-m MODE, --mode MODE: 选择不同的模式，如银行卡、发票、身份证等。
-b BATCH, --batch BATCH: 指定处理的批量大小。
-l LANG, --lang LANG: 指定文本的语言类型。
--clear_output: 清空特定模式的输出文件夹下的所有内容。
```

示例

```bash
python tis -m bankcard -b 10 -l en
```

## 贡献

欢迎贡献代码或提出建议。如果您发现了 Bug 或有改进建议，请在 GitHub 上提交 issue。

## 许可证

本项目基于 MIT 许可证。详情请参阅 LICENSE 文件。
