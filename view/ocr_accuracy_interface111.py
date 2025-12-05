import os
from natsort import natsorted
import shutil
import json
from PyQt5.QtCore import Qt, QPoint, QPointF, QEvent, QSettings,QRegExp
from PyQt5.QtGui import QPolygonF, QFont, QPalette, QColor,QRegExpValidator
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, 
                           QGroupBox, QFileDialog, QMessageBox,QTextBrowser,QDialog)


from common.utils import Utils
from components.image_canvas import PolygonsDrawImageCanvas



class OCRAccuracyTool(QWidget):

    """OCR精度调整工具模块，用于调整OCR识别区域的多边形标注"""

    status_updated = pyqtSignal(str, str)
    name_updated = pyqtSignal(str)
    count_updated = pyqtSignal(int, int)
    scale_updated = pyqtSignal(float)  # 缩放比例更新信号

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = QSettings("AnnotationTool", "OCRAccuracyTool")
        self.file_pairs = [] # 存储图像和 JSON 文件对的列表
        self.current_index = -1  # 当前文件的索引，初始值为 -1 表示未选中
        self.shift_pressed = False # 标记Shift键是否被按下
        self.n_pressed = False # 标记N键是否被按下
        self.show_polygons = True  # 默认显示多边形

        self.setObjectName("ocr_accuracy_interface")

        self.init_ui()
        self.init_vars()

    def init_vars(self):
        """初始化变量（适配新层级）"""
        self.JsonDataList = None  # 根数据对象
        self.creating_poly = False
        self.current_poly = []
        self.selected_charset_index = -1  # 选中的Charset索引（扁平化索引）
        self.selected_vertex = -1 # 选中的顶点索引（扁平化索引）
        self.dragging_vertex = False
        self.dragging_poly = False
        self.drag_start_pos = QPointF()
        self.poly_original_pos = []
        self.poly_colors = []  # 每个Charset的颜色
        
        # 清空UI输入
        self.vertex_idx.clear()
        self.vertex_x.clear()
        self.vertex_y.clear()
        self.poly_id.clear()
        self.poly_text.clear()
        self.poly_lang.clear()



    def init_ui(self):
        """初始化UI"""
        main_layout = QHBoxLayout(self)
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_panel.setFixedWidth(400)
        
        dir_group = QGroupBox("文件夹设置")
        dir_layout = QVBoxLayout()

        # 图片路径
        img_dir_layout = QHBoxLayout()
        image_label = QLabel("图片文件路径:")
        image_label.setFixedWidth(80)
        self.images_dir = QLineEdit()
        self.images_dir.setText(self.settings.value("ocr_accuracy_tool_images_dir", ""))
        img_browse_btn = QPushButton("浏览")
        img_browse_btn.clicked.connect(self.browse_images_dir)
        img_dir_layout.addWidget(image_label)
        img_dir_layout.addWidget(self.images_dir)
        img_dir_layout.addWidget(img_browse_btn)


        
        # JSON路径
        json_dir_layout = QHBoxLayout()
        json_label = QLabel("JSON文件路径:")
        json_label.setFixedWidth(80)
        self.jsons_dir = QLineEdit()
        self.jsons_dir.setText(self.settings.value("ocr_accuracy_tool_jsons_dir", ""))
        json_browse_btn = QPushButton("浏览")
        json_browse_btn.clicked.connect(self.browse_jsons_dir)
        json_dir_layout.addWidget(json_label)
        json_dir_layout.addWidget(self.jsons_dir)
        json_dir_layout.addWidget(json_browse_btn)
        

        match_btn = QPushButton("匹配文件对")
        match_btn.clicked.connect(self.match_file_pairs)
        
        dir_layout.addLayout(img_dir_layout)
        dir_layout.addLayout(json_dir_layout)
        dir_layout.addWidget(match_btn)
        dir_group.setLayout(dir_layout)
        control_layout.addWidget(dir_group)
        
        btn_group = QGroupBox("操作控制")
        btn_layout = QVBoxLayout()
        

        btn_row1 = QHBoxLayout()
        create_poly_btn = QPushButton("新建多边形")
        finish_poly_btn = QPushButton("完成多边形")
        delete_selected_btn = QPushButton("删除选中")
        delete_selected_btn.setShortcut("Delete")
        clear_all_btn = QPushButton("清空所有")

        create_poly_btn.clicked.connect(self.on_Key_N_pressed)
        finish_poly_btn.clicked.connect(self.on_Key_N_pressed)
        delete_selected_btn.clicked.connect(self.delete_selected)
        clear_all_btn.clicked.connect(self.clear_all)

        btn_row1.addWidget(create_poly_btn)
        btn_row1.addWidget(finish_poly_btn)
        btn_row1.addWidget(delete_selected_btn)
        btn_row1.addWidget(clear_all_btn)
        
        btn_row2 = QHBoxLayout()
        save_btn = QPushButton("保存标注")
        save_btn.setShortcut("Ctrl+S")
        delete_btn = QPushButton("删除标注")
        reset_view_btn = QPushButton("重置视图")
        reset_view_btn.setShortcut("Space")
        reset_label_btn = QPushButton("重置数据")

        save_btn.clicked.connect(self.save_annotations)
        reset_view_btn.clicked.connect(self.reset_view)
        delete_btn.clicked.connect(self.delete_annotations)
        reset_label_btn.clicked.connect(self.reset_labels)

        btn_row2.addWidget(save_btn)
        btn_row2.addWidget(delete_btn)
        btn_row2.addWidget(reset_view_btn)
        btn_row2.addWidget(reset_label_btn)
        
        # 跳转控制
        go_layout = QHBoxLayout()
        go_label1 = QLabel("图片序号：")
        go_label1.setFixedWidth(50)
        self.go_text = QLineEdit()
        self.go_text.setValidator(QRegExpValidator(QRegExp("[1-9][0-9]*")))
        update_go_btn = QPushButton("跳转")
        update_go_btn.clicked.connect(self.go_to_image)
        go_layout.addWidget(go_label1)
        go_layout.addWidget(self.go_text, 1)
        go_layout.addWidget(update_go_btn)
        go_layout.addStretch()



        # 快捷键说明
        btn_row3 = QHBoxLayout()
        shortcut_btn = QPushButton("快捷键说明")
        shortcut_btn.clicked.connect(self.show_shortcut_help)
        btn_row3.addWidget(shortcut_btn)

        btn_layout.addLayout(btn_row1)
        btn_layout.addLayout(btn_row2)
        btn_layout.addLayout(go_layout)
        btn_layout.addLayout(btn_row3)
        btn_group.setLayout(btn_layout)
        control_layout.addWidget(btn_group)
        
    
        # 多边形属性
        prop_group = QGroupBox("Charset属性")
        prop_layout = QVBoxLayout()

        id_layout = QHBoxLayout()
        id_label = QLabel("ID:")
        id_label.setFixedWidth(40)
        self.poly_id = QLineEdit()
        self.poly_id.setReadOnly(True)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.poly_id)
        
        text_layout = QHBoxLayout()
        text_label = QLabel("文本:")
        text_label.setFixedWidth(40)
        self.poly_text = QLineEdit()
        update_text_btn = QPushButton("更新文本")
        update_text_btn.clicked.connect(self.update_poly_text)
        text_layout.addWidget(text_label)
        text_layout.addWidget(self.poly_text)
        text_layout.addWidget(update_text_btn)
        
        lang_layout = QHBoxLayout()
        lang_label = QLabel("语言:")
        lang_label.setFixedWidth(40)
        self.poly_lang = QLineEdit()
        update_lang_btn = QPushButton("更新语言")
        update_lang_btn.clicked.connect(self.update_poly_language)
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.poly_lang)
        lang_layout.addWidget(update_lang_btn)
        
        prop_layout.addLayout(id_layout)
        prop_layout.addLayout(text_layout)
        prop_layout.addLayout(lang_layout)
        prop_group.setLayout(prop_layout)
        control_layout.addWidget(prop_group)
        
      
        # 顶点编辑
        vertex_group = QGroupBox("顶点编辑")
        vertex_layout = QHBoxLayout()
        self.vertex_idx = QLineEdit()
        self.vertex_idx.setReadOnly(True)
        self.vertex_idx.setMaximumWidth(50)
        self.vertex_x = QLineEdit()
        self.vertex_x.setMaximumWidth(70)
        self.vertex_y = QLineEdit()
        self.vertex_y.setMaximumWidth(70)
        apply_vertex_btn = QPushButton("应用")
        apply_vertex_btn.clicked.connect(self.apply_vertex_coords)
        
        vertex_layout.addWidget(QLabel("顶点索引:"))
        vertex_layout.addWidget(self.vertex_idx)
        vertex_layout.addWidget(QLabel("X:"))
        vertex_layout.addWidget(self.vertex_x)
        vertex_layout.addWidget(QLabel("Y:"))
        vertex_layout.addWidget(self.vertex_y)
        vertex_layout.addWidget(apply_vertex_btn)
        vertex_group.setLayout(vertex_layout)
        control_layout.addWidget(vertex_group)
        control_layout.addStretch() # 控制布局添加弹性空间，用于调整按钮组与右侧显示区域的间距
        # 右侧显示区域
        display_group = QGroupBox("标注区域 (拖动顶点调整形状，右键拖动图像，滚轮缩放)")
        canvas_layout = QVBoxLayout()
        self.canvas = PolygonsDrawImageCanvas(self)
        self.canvas.key_Shift_pressed.connect(self.on_shift_pressed)
        self.canvas.key_D_pressed.connect(self.on_d_pressed)
        self.canvas.Key_Left_pressed.connect(self.on_Key_Left_pressed)
        self.canvas.Key_Right_pressed.connect(self.on_Key_Right_pressed)
        self.canvas.Key_N_pressed.connect(self.on_Key_N_pressed)
        self.canvas.Key_ESCAPE_pressed.connect(self.on_Key_ESCAPE_pressed)

        canvas_layout.addWidget(self.canvas)
        display_group.setLayout(canvas_layout)
        main_layout.addWidget(control_panel)
        main_layout.addWidget(display_group, 1)

        # 重写画布事件
        self.original_mousePressEvent = self.canvas.mousePressEvent
        self.original_mouseMoveEvent = self.canvas.mouseMoveEvent
        self.original_mouseReleaseEvent = self.canvas.mouseReleaseEvent
        self.canvas.mousePressEvent = self.on_canvas_click
        self.canvas.mouseMoveEvent = self.on_canvas_drag
        self.canvas.mouseReleaseEvent = self.on_canvas_release

    

    def browse_images_dir(self):
        """浏览图片文件夹"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if dir_path:
            self.images_dir.setText(dir_path)
            
    def browse_jsons_dir(self):
        """浏览JSON文件夹"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择JSON文件夹")
        if dir_path:
            self.jsons_dir.setText(dir_path)
            
    def match_file_pairs(self):
        """匹配图片和JSON文件对"""
        images_dir = self.images_dir.text()
        jsons_dir = self.jsons_dir.text()
        
        if not os.path.isdir(images_dir) or not os.path.isdir(jsons_dir):
            QMessageBox.warning(self, "警告", "请选择有效的图片和JSON文件夹")
            return
        
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        image_files = [f for f in os.listdir(images_dir) 
                      if os.path.isfile(os.path.join(images_dir, f)) 
                      and os.path.splitext(f)[1].lower() in image_extensions]
        
        # 匹配对应的JSON文件
        self.file_pairs = []
        for img_file in natsorted(image_files):
            base_name = os.path.splitext(img_file)[0]
            json_file = f"{base_name}.json"
            json_path = os.path.join(jsons_dir, json_file)
            if os.path.exists(json_path):
                self.file_pairs.append({
                    'image': os.path.join(images_dir, img_file),
                    'json': json_path
                })

        self.settings.setValue("ocr_accuracy_tool_images_dir", images_dir)
        self.settings.setValue("ocr_accuracy_tool_jsons_dir", jsons_dir)

        if self.file_pairs:
            print(f"已匹配 {len(self.file_pairs)} 对文件")
            print(self.file_pairs)
            self.status_updated.emit(f"已匹配 {len(self.file_pairs)} 对文件", "green")
            self.current_index = 0
            self.load_current_file()
        else:
            QMessageBox.warning(self, "警告", "未找到匹配的文件对")
            self.status_updated.emit("未找到匹配的文件对", "red")
    
    def load_current_file(self):
        """加载当前文件"""

        if 0 <= self.current_index < len(self.file_pairs):
            file_pair = self.file_pairs[self.current_index]
            self.canvas.load_image(file_pair['image'])
            self.load_annotations(file_pair['json'])
            self.update_status()


    def update_status(self):
        """更新进度标签（当前图像索引/总数量）"""
        if self.file_pairs:
            self.count_updated.emit(self.current_index + 1, len(self.file_pairs))
            self.name_updated.emit(os.path.basename(self.file_pairs[self.current_index]['image']))
        self.scale_updated.emit(self.canvas.scale)

            
    def load_annotations(self, json_path):
        """加载标注数据"""

        self.init_vars()
        
        if os.path.exists(json_path):
            try:

                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)


                json_data_list_info = []
                for item in data.get('DataList',[]):

                    charsets  = []
                    for charset_dict in item.get('charsets', []):
                        poly = [QPointF(p[0], p[1]) for p in charset_dict.get('poly', [])[0]]
                        text = charset_dict.get("text", "")
                        confidence = charset_dict.get("confidence", 0.0)
                        charsets.append(JsonCharsetInfo(poly, text, confidence))

                    # 解析JsonDataListInfo
                    id = item.get("id", "")
                    text = item.get("text", "")
                    poly = [QPointF(p[0], p[1]) for p in item.get('poly', [])]
                    language = item.get('language', '')
                    json_data_list_info.append(JsonDataListInfo(id, text, language, poly, charsets))

                # 创建根数据对象
                self.JsonDataList = JsonDataList(
                    FilePath=data.get("FilePath", ""),
                    Source=data.get("Source", ""),
                    data_list=json_data_list_info
                )
                

                self.poly_colors = [Utils.generate_random_color() for _ in self.JsonDataList.all_charsets]
                self.canvas.poly_colors = self.poly_colors


                print(self.JsonDataList)

                # 更新画布显示
                self.update_canvas_polygons()
                self.canvas.update()

                # 自动选中第一个Charset
                if self.JsonDataList.all_charsets:
                    self.selected_charset_index = 0
                    self.update_charset_property_display()
                
            except Exception as e:
                self.status_updated.emit(f"加载标注失败: {str(e)}", "red")
            
    def update_canvas_polygons(self):
        """更新画布上的多边形（只显示Charset的poly）"""
        if not self.JsonDataList:
            self.canvas.polygons = []
            return

        if self.show_polygons:
            # 显示所有Charset的poly + 当前正在创建的poly
            if self.creating_poly and self.current_poly:
                self.canvas.polygons = self.JsonDataList.charsets_poly_list + [self.current_poly]
            else:
                self.canvas.polygons = self.JsonDataList.charsets_poly_list
        else:
            self.canvas.polygons = []

        # 更新颜色列表（包含正在创建的poly）
        if self.creating_poly and self.current_poly:
            self.canvas.poly_colors = self.poly_colors + [QColor(0, 255, 255, 150)]
        else:
            self.canvas.poly_colors = self.poly_colors


    def update_charset_property_display(self):
        """更新选中Charset的属性显示"""
        if self.selected_charset_index < 0 or not self.JsonDataList:
            self.poly_id.clear()
            self.poly_text.clear()
            self.poly_lang.clear()
            return

        # 获取选中的Charset及其所属的DataListInfo
        data_info, data_index, charset_subindex = self.JsonDataList.get_charset_by_index(self.selected_charset_index)
        if not data_info:
            return

        # 显示属性
        self.poly_id.setText(f"{data_info.id}_{charset_subindex}")  # 组合ID（DataListInfoID_Charset索引）
        self.poly_text.setText(self.JsonDataList.all_charsets[self.selected_charset_index].text)
        self.poly_lang.setText(data_info.language)

        # 更新顶点信息（如果有选中的顶点）
        if self.selected_vertex >= 0:
            charset = self.JsonDataList.all_charsets[self.selected_charset_index]
            if 0 <= self.selected_vertex < len(charset.poly):
                point = charset.poly[self.selected_vertex]
                self.vertex_idx.setText(str(self.selected_vertex))
                self.vertex_x.setText(f"{point.x():.1f}")
                self.vertex_y.setText(f"{point.y():.1f}")
            else:
                self.vertex_idx.clear()
                self.vertex_x.clear()
                self.vertex_y.clear()


    def on_canvas_click(self, event):
        """画布点击事件（适配Charset层级）"""
        if not self.JsonDataList:
            self.original_mousePressEvent(event)
            return

        # 转换坐标到图像坐标系
        x = (event.pos().x() - self.canvas.offset.x()) / self.canvas.scale
        y = (event.pos().y() - self.canvas.offset.y()) / self.canvas.scale
        click_point = QPointF(x, y)

        # 正在创建多边形
        if self.creating_poly and event.button() == Qt.LeftButton:
            self.add_create_poly_vertex(click_point)
            return

        # Shift键添加顶点
        if self.shift_pressed and event.button() == Qt.LeftButton:
            self.add_vertex_to_charset_edge(click_point)
            return

        # 点击顶点
        if event.button() == Qt.LeftButton:
            vertex_clicked = self.check_vertex_click(click_point)
            if vertex_clicked:
                return

            # 点击多边形内部
            poly_clicked = self.check_poly_click(click_point)
            if poly_clicked:
                return

            # 未点击任何元素
            self.selected_charset_index = -1
            self.selected_vertex = -1
            self.canvas.selected_item = -1
            self.update_charset_property_display()
            self.canvas.update()

        self.original_mousePressEvent(event)


    def add_create_poly_vertex(self, click_point):
        """添加创建多边形的顶点"""
        if self.canvas.image is None:
            self.status_updated.emit("请先加载图片", "red")
            return

        # 限制在图片范围内
        img_width = self.canvas.image.width()
        img_height = self.canvas.image.height()
        clamped_point = QPointF(
            max(0, min(click_point.x(), img_width)),
            max(0, min(click_point.y(), img_height))
        )

        self.current_poly.append(clamped_point)
        self.update_canvas_polygons()
        self.canvas.update()
        self.status_updated.emit(f"已添加顶点 ({clamped_point.x():.1f}, {clamped_point.y():.1f})，继续点击添加或完成", "white")

    def check_vertex_click(self, click_point):
        """检查是否点击了顶点"""
        all_charsets = self.JsonDataList.all_charsets
        threshold = 10 / self.canvas.scale

        for i, charset in enumerate(all_charsets):
            for j, point in enumerate(charset.poly):
                dist = ((point.x() - click_point.x())**2 + (point.y() - click_point.y())**2)**0.5
                if dist < threshold:
                    # 选中该顶点
                    self.selected_charset_index = i
                    self.selected_vertex = j
                    self.canvas.selected_item = i
                    self.dragging_vertex = True
                    self.update_charset_property_display()
                    self.canvas.update()
                    return True
        return False

    def check_poly_click(self, click_point):
        """检查是否点击了多边形内部"""
        all_charsets = self.JsonDataList.all_charsets

        for i, charset in enumerate(all_charsets):
            if not charset.poly:
                continue
            q_poly = QPolygonF(charset.poly)
            if q_poly.containsPoint(click_point, Qt.OddEvenFill):
                # 选中该多边形
                self.selected_charset_index = i
                self.selected_vertex = -1
                self.canvas.selected_item = i
                self.dragging_poly = True
                self.drag_start_pos = click_point
                # 保存原始位置
                self.poly_original_pos = [QPointF(p.x(), p.y()) for p in charset.poly]
                self.update_charset_property_display()
                self.canvas.update()
                return True
        return False

    def add_vertex_to_charset_edge(self, click_point):
        """在Charset的边上添加顶点"""
        all_charsets = self.JsonDataList.all_charsets
        threshold = 2 / self.canvas.scale
        best_charset_idx = -1
        best_edge_idx = -1
        min_dist = float("inf")

        for i, charset in enumerate(all_charsets):
            poly = charset.poly
            if len(poly) < 2:
                continue
            for j in range(len(poly)):
                p1 = poly[j]
                p2 = poly[(j + 1) % len(poly)]
                dist = self.point_to_line_distance(click_point, p1, p2)
                if dist < threshold and dist < min_dist:
                    min_dist = dist
                    best_charset_idx = i
                    best_edge_idx = j + 1  # 插入到边的后面

        if best_charset_idx != -1:
            # 插入新顶点
            charset = all_charsets[best_charset_idx]
            charset.poly.insert(best_edge_idx, click_point)
            self.selected_charset_index = best_charset_idx
            self.selected_vertex = -1
            self.canvas.selected_item = best_charset_idx
            self.update_canvas_polygons()
            self.canvas.update()
            self.update_charset_property_display()
            self.status_updated.emit(f"已在Charset {best_charset_idx} 的边上添加顶点", "white")

    def on_canvas_drag(self, event):
        """画布拖动事件（适配Charset层级）"""
        if not self.JsonDataList:
            self.original_mouseMoveEvent(event)
            return

        # 转换坐标
        x = (event.pos().x() - self.canvas.offset.x()) / self.canvas.scale
        y = (event.pos().y() - self.canvas.offset.y()) / self.canvas.scale
        current_point = QPointF(x, y)

        # 拖动顶点
        if self.dragging_vertex:
            self.drag_vertex(current_point)
            return

        # 拖动多边形
        if self.dragging_poly:
            self.drag_charset_poly(current_point)
            return

        # 创建多边形时的预览
        if self.creating_poly:
            self.preview_create_poly(current_point)
            return

        self.original_mouseMoveEvent(event)

    def drag_vertex(self, current_point):
        """拖动顶点"""
        if self.selected_charset_index < 0 or self.selected_vertex < 0:
            return

        # 限制在图片范围内
        if self.canvas.image:
            img_width = self.canvas.image.width()
            img_height = self.canvas.image.height()
            clamped_x = max(0, min(current_point.x(), img_width))
            clamped_y = max(0, min(current_point.y(), img_height))
        else:
            clamped_x = current_point.x()
            clamped_y = current_point.y()

        # 更新顶点位置
        charset = self.JsonDataList.all_charsets[self.selected_charset_index]
        charset.poly[self.selected_vertex] = QPointF(clamped_x, clamped_y)

        # 更新UI
        self.vertex_x.setText(f"{clamped_x:.1f}")
        self.vertex_y.setText(f"{clamped_y:.1f}")
        self.update_canvas_polygons()
        self.canvas.update()

    def drag_charset_poly(self, current_point):
        """拖动整个Charset多边形"""
        if self.selected_charset_index < 0:
            return

        # 计算偏移量
        dx = current_point.x() - self.drag_start_pos.x()
        dy = current_point.y() - self.drag_start_pos.y()

        # 限制在图片范围内
        if self.canvas.image:
            img_width = self.canvas.image.width()
            img_height = self.canvas.image.height()
        else:
            img_width = float('inf')
            img_height = float('inf')

        # 更新所有顶点
        charset = self.JsonDataList.all_charsets[self.selected_charset_index]
        new_poly = []
        for i, (orig_p, curr_p) in enumerate(zip(self.poly_original_pos, charset.poly)):
            new_x = orig_p.x() + dx
            new_y = orig_p.y() + dy
            # 限制范围
            new_x = max(0, min(new_x, img_width))
            new_y = max(0, min(new_y, img_height))
            new_poly.append(QPointF(new_x, new_y))

        charset.poly = new_poly
        self.update_canvas_polygons()
        self.canvas.update()

    def preview_create_poly(self, current_point):
        """预览正在创建的多边形"""
        if not self.current_poly:
            return
        original_poly = self.current_poly.copy()
        self.current_poly.append(current_point)
        self.update_canvas_polygons()
        self.canvas.update()
        self.current_poly = original_poly

    def on_canvas_release(self, event):
        """画布释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging_vertex = False
            self.dragging_poly = False
        self.original_mouseReleaseEvent(event)

    def start_create_poly(self):
        """开始创建多边形"""
        self.creating_poly = True
        self.canvas.setMouseTracking(True)
        self.canvas.setCursor(Qt.CrossCursor)
        self.current_poly = []
        self.status_updated.emit("请在图像上点击添加多边形顶点，完成后点击'完成多边形'", "white")

    def finish_create_poly(self):
        """完成创建多边形（添加为新的Charset）"""
        if len(self.current_poly) < 3:
            QMessageBox.warning(self, "警告", "多边形至少需要3个顶点")
            return

        # 创建新的Charset
        new_charset = JsonCharsetInfo(
            poly=self.current_poly.copy(),
            text="",
            confidence=0.0
        )

        # 如果没有DataListInfo，创建一个默认的
        if not self.JsonDataList.data_list:
            default_data_info = JsonDataListInfo(
                id=f"Data_{len(self.JsonDataList.data_list)}",
                text="",
                language="",
                poly=[],
                charsets=[new_charset]
            )
            self.JsonDataList.add_data_list_info(default_data_info)
        else:
            # 添加到最后一个DataListInfo中
            last_data_info = self.JsonDataList.data_list[-1]
            last_data_info.add_charset(new_charset)

        # 更新状态
        self.poly_colors.append(Utils.generate_random_color())
        self.creating_poly = False
        self.current_poly = []
        self.canvas.setMouseTracking(False)
        self.canvas.setCursor(Qt.ArrowCursor)

        # 选中新创建的Charset
        self.selected_charset_index = len(self.JsonDataList.all_charsets) - 1
        self.selected_vertex = -1
        self.canvas.selected_item = self.selected_charset_index

        # 更新画布
        self.update_canvas_polygons()
        self.canvas.poly_colors = self.poly_colors
        self.canvas.update()
        self.update_charset_property_display()
        self.status_updated.emit(f"已创建Charset，共 {len(self.JsonDataList.all_charsets)} 个", "white")

    def cancel_create_poly(self):
        """取消创建多边形"""
        self.creating_poly = False
        self.current_poly = []
        self.canvas.setCursor(Qt.ArrowCursor)
        self.canvas.setMouseTracking(False)
        self.update_canvas_polygons()
        self.canvas.update()
        self.status_updated.emit("已取消新建多边形", "white")

    def delete_selected(self):
        """删除选中的Charset"""
        if self.selected_charset_index < 0 or not self.JsonDataList:
            return

        # 获取选中的Charset及其所属的DataListInfo
        data_info, data_index, charset_subindex = self.JsonDataList.get_charset_by_index(self.selected_charset_index)
        if not data_info:
            return

        # 删除Charset
        data_info.remove_charset(charset_subindex)

        # 如果DataListInfo没有Charset了，删除该DataListInfo
        if not data_info.charsets:
            self.JsonDataList.remove_data_list_info(data_index)

        # 更新颜色列表
        del self.poly_colors[self.selected_charset_index]

        # 更新选中状态
        self.selected_charset_index = -1
        self.selected_vertex = -1
        self.canvas.selected_item = -1

        # 更新画布
        self.update_canvas_polygons()
        self.canvas.poly_colors = self.poly_colors
        self.canvas.update()
        self.update_charset_property_display()
        self.status_updated.emit(f"已删除选中Charset，剩余 {len(self.JsonDataList.all_charsets)} 个", "white")

    def clear_all(self):
        """清空所有Charset和DataListInfo"""
        if not self.JsonDataList or not self.JsonDataList.all_charsets:
            return

        reply = QMessageBox.question(self, "确认", "确定要清空所有标注吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.JsonDataList = JsonDataList(FilePath="", Source="", data_list=[])
            self.init_vars()
            self.update_canvas_polygons()
            self.canvas.update()
            self.status_updated.emit("已清空所有标注", "white")

    def save_annotations(self):

        """保存标注（适配新的JSON层级结构）"""
        if self.current_index < 0 or not self.file_pairs or not self.JsonDataList:
            return
        
        json_path = self.file_pairs[self.current_index]['json']
        image_path = self.file_pairs[self.current_index]['image']

        # 构建JSON数据
        json_data = {
            "FilePath": os.path.basename(image_path),
            "Source": self.JsonDataList._Source,
            "DataList": []
        }

        # 遍历每个DataListInfo
        for data_info in self.JsonDataList.data_list:
            data_item = {
                "id": data_info.id,
                "text": data_info.text,
                "language": data_info.language,
                "poly": [[p.x(), p.y()] for p in data_info.poly],
                "charsets": []
            }

            # 遍历每个Charset
            for charset in data_info.charsets:
                data_item["charsets"].append({
                    "poly": [[[p.x(), p.y()] for p in charset.poly]],
                    "text": charset.text,
                    "confidence": charset.confidence
                })

            json_data["DataList"].append(data_item)

        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            self.status_updated.emit("标注已保存", "green")
        except Exception as e:
            self.status_updated.emit(f"保存标注失败: {str(e)}", "red")


    def update_poly_text(self):
        """更新选中Charset的文本"""
        if self.selected_charset_index < 0 or not self.JsonDataList:
            return

        charset = self.JsonDataList.all_charsets[self.selected_charset_index]
        charset.text = self.poly_text.text()
        self.status_updated.emit("Charset文本已更新", "white")

    def update_poly_language(self):
        """更新选中Charset所属DataListInfo的语言"""
        if self.selected_charset_index < 0 or not self.JsonDataList:
            return

        data_info, _, _ = self.JsonDataList.get_charset_by_index(self.selected_charset_index)
        if data_info:
            data_info.language = self.poly_lang.text()
            self.status_updated.emit("语言已更新", "white")

    
    def apply_vertex_coords(self):
        """应用顶点坐标修改"""
        if self.selected_charset_index < 0 or self.selected_vertex < 0 or not self.JsonDataList:
            return

        try:
            x = float(self.vertex_x.text())
            y = float(self.vertex_y.text())

            # 限制在图片范围内
            if self.canvas.image:
                x = max(0, min(x, self.canvas.image.width()))
                y = max(0, min(y, self.canvas.image.height()))

            # 更新顶点
            charset = self.JsonDataList.all_charsets[self.selected_charset_index]
            charset.poly[self.selected_vertex] = QPointF(x, y)

            # 更新画布
            self.update_canvas_polygons()
            self.canvas.update()
            self.status_updated.emit("顶点坐标已更新", "white")
        except ValueError:
            self.status_updated.emit("顶点坐标必须是数字", "red")

    
    def on_d_pressed(self):
        """删除选中的顶点"""
        if self.selected_charset_index < 0 or self.selected_vertex < 0 or not self.JsonDataList:
            return

        charset = self.JsonDataList.all_charsets[self.selected_charset_index]
        if len(charset.poly) <= 3:
            QMessageBox.warning(self, "警告", "多边形至少需要3个顶点")
            return

        # 删除顶点
        charset.remove_poly(self.selected_vertex)
        self.selected_vertex = -1
        self.vertex_idx.clear()
        self.vertex_x.clear()
        self.vertex_y.clear()

        # 更新画布
        self.update_canvas_polygons()
        self.canvas.update()
        self.status_updated.emit("已删除顶点", "white")

    def on_shift_pressed(self, pressed):
        self.shift_pressed = pressed
        if pressed:
            self.status_updated.emit("Shift键已按下，点击Charset边缘添加顶点", "white")
        else:
            self.status_updated.emit("Shift键已释放", "white")

    def on_Key_N_pressed(self):
        if not self.creating_poly:
            self.start_create_poly()
        else:
            self.finish_create_poly()

    def on_Key_ESCAPE_pressed(self):
        self.cancel_create_poly()
    
    def on_Key_Left_pressed(self):
        if self.file_pairs and self.current_index > 0:
            self.save_annotations()
            self.current_index -= 1
            self.load_current_file()

    def on_Key_Right_pressed(self):
        if self.file_pairs and self.current_index < len(self.file_pairs) - 1:
            self.save_annotations()
            self.current_index += 1
            self.load_current_file()
    
    def toggle_polygons_visibility(self):
        """切换多边形显示/隐藏"""
        self.show_polygons = not self.show_polygons
        self.update_canvas_polygons()
        self.canvas.update()
        status = "已显示" if self.show_polygons else "已隐藏"
        self.status_updated.emit(f"{status}多边形", "white")
            
    
    


    def delete_annotations(self):
        """删除当前图片和JSON文件"""
        if self.current_index < 0 or not self.file_pairs:
            return

        reply = QMessageBox.question(self, "确认", "确定要删除当前图片和JSON文件吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            file_pair = self.file_pairs[self.current_index]
            delete_path = os.path.join(os.path.dirname(file_pair['image']), 'deleted')
            os.makedirs(delete_path, exist_ok=True)

            # 移动文件
            shutil.move(file_pair['json'], os.path.join(delete_path, os.path.basename(file_pair['json'])))
            shutil.move(file_pair['image'], os.path.join(delete_path, os.path.basename(file_pair['image'])))
            
            # 更新文件列表
            self.file_pairs.pop(self.current_index)
            self.init_vars()

            # 加载下一个文件
            self.current_index = max(0, self.current_index - 1)
            if self.file_pairs:
                self.load_current_file()
            else:
                self.canvas.clear()

            self.status_updated.emit("已删除当前图像的标注", "white")



    def go_to_image(self):
        """跳转图片"""
        try:
            index = int(self.go_text.text()) - 1
            if 0 <= index < len(self.file_pairs):
                self.current_index = index
                self.load_current_file()
                self.status_updated.emit(f"跳转至第 {index + 1} 张图片", "white")
            else:
                self.status_updated.emit("图片索引无效", "red")
        except ValueError:
            self.status_updated.emit("请输入有效的数字", "red")

    def reset_labels(self):
        """重置数据"""
        if self.current_index >= 0 and self.file_pairs:
            self.load_annotations(self.file_pairs[self.current_index]['json'])

    def reset_view(self):
        """重置视图"""
        self.canvas.reset_view()


    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_C and self.creating_poly:
            self.cancel_create_poly()
        elif event.key() == Qt.Key_S:
            self.toggle_polygons_visibility()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        """滚轮缩放"""
        self.canvas.wheelEvent(event)
        self.scale_updated.emit(self.canvas.scale)


 
    
    def point_to_line_distance(self, point, line_p1, line_p2):
        """计算点到线段的距离"""
        if line_p1 == line_p2:
            return ((point.x() - line_p1.x())**2 + (point.y() - line_p1.y())**2)**0.5

        line_vec = line_p2 - line_p1
        point_vec = point - line_p1
        line_len_sq = line_vec.x()**2 + line_vec.y()**2
        t = max(0, min(1, (point_vec.x() * line_vec.x() + point_vec.y() * line_vec.y()) / line_len_sq))
        projection = line_p1 + t * line_vec
        return ((point.x() - projection.x())**2 + (point.y() - projection.y())**2)**0.5
        

    def show_shortcut_help(self):
        """显示快捷键说明弹窗"""
        class ShortcutDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("快捷键说明")
                self.setMinimumSize(600, 400)
                self.setModal(True)
                
                self.setStyleSheet("""
                    QDialog { background-color: #f5f5f5; font-family: 'Segoe UI', Arial, sans-serif; }
                    QTextBrowser {
                        background-color: white;
                        border: 1px solid #ddd;
                        border-radius: 6px;
                        padding: 15px;
                        font-size: 14px;
                        line-height: 1.6;
                    }
                    QPushButton {
                        background-color: #4CAF50; color: white; border: none;
                        border-radius: 4px; padding: 8px 16px; font-size: 14px; min-width: 80px;
                    }
                    QPushButton:hover { background-color: #45a049; }
                    QPushButton:pressed { background-color: #3d8b40; }
                """)
                
                layout = QVBoxLayout(self)
                text_browser = QTextBrowser()
                
                shortcut_content = """
                <style>
                    h3 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin-top: 20px; margin-bottom: 15px; }
                    ul { color: #2c3e50; margin: 10px 0; padding-left: 25px; }
                    li { margin: 8px 0; }
                    b { color: #e74c3c; }
                </style>
                
                <h3>一、基础操作快捷键</h3>
                <ul>
                    <li><b>N键开始</b>：新建Charset多边形</li>
                    <li><b>N键结束</b>：完成Charset多边形</li>
                    <li><b>ESC键</b>：取消新建多边形</li>
                    <li><b>DEL键</b>：删除选中的Charset</li>
                    <li><b>CTRL+S</b>：保存当前标注</li>
                    <li><b>S键</b>：切换多边形显示/隐藏</li>
                    <li><b>SPACE键</b>：重置视图（居中显示）</li>
                    <li><b>SHIFT键（长按）</b>：添加顶点（点击Charset边缘）</li>
                    <li><b>D键</b>：删除选中顶点（需先选中顶点）</li>
                    <li><b>LEFT键</b>：切换到上一张图片（自动保存）</li>
                    <li><b>RIGHT键</b>：切换到下一张图片（自动保存）</li>
                </ul>
                
                <h3>二、鼠标操作</h3>
                <ul>
                    <li><b>左键点击</b>：
                        <ul>
                            <li>新建多边形时：添加顶点</li>
                            <li>选中顶点时：拖动调整顶点位置</li>
                            <li>选中Charset内部：拖动整个Charset</li>
                        </ul>
                    </li>
                    <li><b>右键拖动</b>：平移画布</li>
                    <li><b>鼠标滚轮</b>：缩放画布</li>
                </ul>
                """
                text_browser.setHtml(shortcut_content)
                
                close_btn = QPushButton("关闭")
                close_btn.clicked.connect(self.accept)
                
                layout.addWidget(text_browser)
                layout.addWidget(close_btn, alignment=Qt.AlignRight | Qt.AlignBottom)
        
        dialog = ShortcutDialog(self)
        dialog.exec_()


    def closeEvent(self, event):
        """关闭事件"""
        self.settings.setValue("ocr_accuracy_tool_images_dir", self.images_dir.text())
        self.settings.setValue("ocr_accuracy_tool_jsons_dir", self.jsons_dir.text())
        super().closeEvent(event)




