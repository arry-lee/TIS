# 通用表格合成项目
- 合成的表格覆盖了5种场景（如保单、医疗单据、货运单、制造业表单、银行流水单等）
- 表格类型：有线表格、无线表格

## 算法描述

## 项目结构
- config  保存配置文件
- static  保存项目用到的静态资源、背景、字体、标注文件、印章文件等
- data_generator 数据生成器包
  - data_generator.py 银行数据生成
  - fakekeys.py 读取标注文件生成通用表格可用的键值
  - uniform.py 通用表格生成器算法

- post_processor 后处理器包
  - noisemaker.py 噪声
  - seal.py 印章 包括 gen_seal 和 add_seal
  - rotation.py 旋转
  - perspective.py 透视
  - distortion.py 扭曲
  - label.py 写标注文件,显示标注
  - watermark.py 水印
  - random.py 包含以上所有的后处理器的随机参数版本

- utils 没地方放的工具
- awesometable.py 定义了 AwesomeTable (核心)
- factory.py 多线程表格工厂


## 运行方法
1. 安装所需依赖 见 requirements.txt
2. python factory.py [type] [batch]

## 配置描述
post_processor_config.yaml 是后处理器的随机参数范围配置与使用概率配置 详情见具体后处理器函数
