# 图片上传检测功能使用指南

## 功能概述

图片上传检测功能允许用户通过Web界面上传遥感图片，并调用推理服务进行地物分类和变化检测。

## 使用方法

### 1. 访问上传页面
- 在监控系统导航栏中点击"图片上传检测"
- 或直接访问 `http://localhost:8086/upload`

### 2. 选择图片文件
- 点击"选择文件"按钮
- 支持格式：TIF、TIFF、JPG、JPEG、PNG
- 建议使用TIF格式以获得最佳检测效果

### 3. 配置检测选项

#### 检测选项
- **变化检测**: 启用变化检测功能
- **仅变化检测**: 仅进行变化检测，不进行地物分类
- **生成图例**: 在结果图片中生成图例

#### 检测类别
支持以下14种地物类别：
- 森林 (forest)
- 草地 (meadow)
- 裸地 (bare_land)
- 农田 (farm_land)
- 湖泊 (lake)
- 河流 (river)
- 道路 (road)
- 堤岸 (bank)
- 池塘 (pond)
- 房屋 (house)
- 大坝 (dam)
- 拦河坝 (barrage)
- 桥梁 (bridge)
- 大型温室 (large_greenhouse)

### 4. 开始检测
- 点击"开始检测"按钮
- 系统会显示检测进度
- 检测完成后会显示结果

## 检测流程

1. **文件上传**: 图片保存到 `data/uploaded_images/` 目录
2. **参数准备**: 根据用户选择配置检测参数
3. **调用推理API**: 向 `http://127.0.0.1:8085/detect/with_data_base_plate` 发送请求
4. **结果处理**: 接收检测结果并展示

## 结果展示

### 检测结果图片
- 显示检测生成的图片
- 支持缩略图预览
- 提供下载链接

### 检测结果数据
- JSON格式的详细检测结果
- 包含地物分类统计
- 变化检测信息（如果启用）

## 技术细节

### API接口
- **上传检测**: `POST /api/upload-and-detect`
- **参数**:
  - `image`: 图片文件
  - `categories`: 检测类别列表（JSON字符串）
  - `is_change_detection`: 是否启用变化检测
  - `is_only_change_detection`: 是否仅变化检测
  - `legend_required`: 是否生成图例

### 文件存储
- 上传图片: `data/uploaded_images/`
- 检测结果: `data/detected_result_images/`
- 结果数据: `data/detected_result_json_files/`

### 推理服务配置
- 推理API地址: `http://127.0.0.1:8085/detect/with_data_base_plate`
- 请求方法: PUT
- 超时时间: 5分钟

## 故障排除

### 常见问题

1. **推理服务连接失败**
   - 检查推理服务是否在 `127.0.0.1:8085` 运行
   - 确认推理API接口可用

2. **文件上传失败**
   - 检查文件格式是否支持
   - 确认文件大小合理
   - 检查磁盘空间

3. **检测超时**
   - 图片分辨率过高可能导致处理时间长
   - 可以尝试压缩图片或降低分辨率

### 日志查看
- 检测过程日志会记录在系统日志中
- 可通过监控系统的"系统运行日志"页面查看

## 开发说明

### 扩展检测类别
在 `templates/upload.html` 中修改类别列表：
```html
<div class="form-check">
    <input class="form-check-input category-checkbox" type="checkbox" value="new_category">
    <label class="form-check-label">新类别</label>
</div>
```

### 修改推理API地址
在 `monitor_web.py` 中修改API地址：
```python
response = requests.put(
    "http://your-api-address/detect/with_data_base_plate",
    json=detect_data,
    timeout=300
)
```

### 自定义结果展示
在 `templates/upload.html` 的 `displayResult` 函数中修改结果展示逻辑。 