import os
from natsort import natsorted
import shutil
import json
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, 
                           QGroupBox, QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, 
                           QAbstractItemView,QApplication, QStyledItemDelegate, QStyleOptionViewItem,
                           QStyle,QTextBrowser,QDialog,QSpinBox)

from common.utils import Utils
from common.base_components import ImageCanvas



from PyQt5.QtCore import Qt, QPoint, QPointF, QEvent, QSettings,QRegExp


from PyQt5.QtGui import QPolygonF, QFont, QPalette, QColor, QIcon,QRegExpValidator


from PyQt5.QtCore import pyqtSignal

class OCRAccuracyTool(QWidget):

    """OCR精度调整工具模块，用于调整OCR识别区域的多边形标注"""

    status_updated = pyqtSignal(str, str)
    name_updated = pyqtSignal(str)
    count_updated = pyqtSignal(int, int)
    scale_updated = pyqtSignal(float)  # 缩放比例更新信号

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.parent = parent
        self.settings = QSettings("AnnotationTool", "OCRAccuracyTool")
        
        self.file_pairs = [] # 存储图像和 JSON 文件对的列表
        self.current_index = -1  # 当前文件的索引，初始值为 -1 表示未选中
        self.poly_colors = []  # 存储每个多边形的颜色
        self.shift_pressed = False # 标记Shift键是否被按下
        self.n_pressed = False # 标记N键是否被按下
        self.show_polygons = True  # 默认显示多边形
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QHBoxLayout(self)
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)

        control_panel.setFixedWidth(400)
        
        dir_group = QGroupBox("文件夹设置")
        dir_layout = QVBoxLayout()

        img_dir_layout = QHBoxLayout()
        image_label = QLabel("图片文件路径:")
        image_label.setFixedWidth(80)

        self.images_dir = QLineEdit()
        if self.settings.value("ocr_accuracy_tool_images_dir") is not None:
            self.images_dir.setText(self.settings.value("ocr_accuracy_tool_images_dir"))
        else:
            self.images_dir.setText(r"")
        img_browse_btn = QPushButton("浏览")
        img_browse_btn.clicked.connect(self.browse_images_dir)
        img_dir_layout.addWidget(image_label)
        img_dir_layout.addWidget(self.images_dir)
        img_dir_layout.addWidget(img_browse_btn)
        
        json_dir_layout = QHBoxLayout()
        json_label = QLabel("JSON文件路径:")
        json_label.setFixedWidth(80)
        self.jsons_dir = QLineEdit()
        if self.settings.value("ocr_accuracy_tool_jsons_dir") is not None:
            self.jsons_dir.setText(self.settings.value("ocr_accuracy_tool_jsons_dir"))
        else:
            self.jsons_dir.setText(r"")
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
        
        go_layout = QHBoxLayout()
        go_label1 = QLabel("图片序号：")
        go_label1.setFixedWidth(50)
        self.go_text = QLineEdit()
        self.go_text.setValidator(QRegExpValidator(QRegExp("[1-9][0-9]*")))

        update_go_btn = QPushButton("跳转")
        update_go_btn.clicked.connect(self.go_to_image)
        go_layout.addWidget(go_label1)
        go_layout.addWidget(self.go_text,1)
        go_layout.addWidget(update_go_btn)
        go_layout.addStretch()

        btn_row3 = QHBoxLayout()
        shortcut_btn = QPushButton("快捷键说明")
        shortcut_btn.clicked.connect(self.show_shortcut_help)  # 绑定弹窗显示事件
        btn_row3.addWidget(shortcut_btn)

        btn_layout.addLayout(btn_row1)
        btn_layout.addLayout(btn_row2)
        
        btn_layout.addLayout(go_layout)
        btn_layout.addLayout(btn_row3)

        btn_group.setLayout(btn_layout)

        control_layout.addWidget(btn_group)
        
    
        prop_group = QGroupBox("多边形属性")
        prop_layout = QVBoxLayout()

        id_layout = QHBoxLayout()
        id_label = QLabel("ID:")
        id_label.setFixedWidth(40)
        self.poly_id = QLineEdit()
        self.poly_id.setReadOnly(True)# 多边形ID文本框设置为只读
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
        # delete_vertex_btn = QPushButton("删除顶点")
        # delete_vertex_btn.clicked.connect(self.on_d_pressed)
        
        vertex_layout.addWidget(QLabel("顶点索引:"))
        vertex_layout.addWidget(self.vertex_idx)
        vertex_layout.addWidget(QLabel("X:"))
        vertex_layout.addWidget(self.vertex_x)
        vertex_layout.addWidget(QLabel("Y:"))
        vertex_layout.addWidget(self.vertex_y)
        vertex_layout.addWidget(apply_vertex_btn)
        #vertex_layout.addWidget(delete_vertex_btn)
        vertex_group.setLayout(vertex_layout)
        control_layout.addWidget(vertex_group)
        
        # 多边形列表
        list_group = QGroupBox("多边形列表 (长按Q键点击多边形添加顶点)")
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        
        self.poly_tree = TabNavigationTreeWidget()
        self.poly_tree.setHeaderLabels(['ID', '文本', '顶点', '语言'])
        self.poly_tree.setColumnWidth(0, 50)    # ID列
        self.poly_tree.setColumnWidth(1, 190)  # 文本列
        self.poly_tree.setColumnWidth(2, 40)    # 顶点数列
        self.poly_tree.setColumnWidth(3, 70)    # 语言列
        self.poly_tree.itemSelectionChanged.connect(self.on_tree_select)


        self.tree_delegate = CustomTreeDelegate(self.poly_tree)  # 父对象设为poly_tree
        self.poly_tree.setItemDelegate(self.tree_delegate)

        list_layout.addWidget(self.poly_tree)
        list_group.setLayout(list_layout)
        control_layout.addWidget(list_group, 1)
        
    
        # 右侧显示区域
        # 创建标注区域的分组框，并设置标题提示信息
        display_group = QGroupBox("标注区域 (拖动顶点调整形状，右键拖动图像，滚轮缩放)")
        canvas_layout = QVBoxLayout()
        self.canvas = ImageCanvas(self)
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

        # 调用初始化变量的函数
        self.init_vars()

        self.original_mousePressEvent = self.canvas.mousePressEvent
        self.original_mouseMoveEvent = self.canvas.mouseMoveEvent
        self.original_mouseReleaseEvent = self.canvas.mouseReleaseEvent

        self.canvas.mousePressEvent = self.on_canvas_click # 重写画布的鼠标按下事件处理函数
        self.canvas.mouseMoveEvent = self.on_canvas_drag # 重写画布的鼠标移动事件处理函数
        self.canvas.mouseReleaseEvent = self.on_canvas_release # 重写画布的鼠标释放事件处理函数

        
    def init_vars(self):
        """初始化变量"""
        self.creating_poly = False  # 是否正在创建多边形
        self.current_poly = []  # 当前正在创建的多边形
        self.poly_data = []  # 所有多边形数据
        self.poly_properties = []  # 多边形属性
        self.poly_colors = []  # 多边形颜色列表
        self.selected_poly = -1  # 标记当前选中的多边形索引，初始值为 -1 表示未选中
        self.selected_vertex = -1  # 标记当前选中的顶点索引，初始值为 -1 表示未选中
        self.dragging_vertex = False  # 标记是否正在拖动顶点，初始值为 False
        self.dragging_poly = False  # 标记是否正在拖动整个多边形，初始值为 False
        self.drag_start_pos = QPoint()  # 拖动开始时的鼠标位置
        self.poly_original_pos = []  # 拖动开始时多边形的原始位置
        self.canvas.poly_colors = self.poly_colors  # 将颜色列表传递给画布
        self.vertex_idx.clear()
        self.vertex_x.clear()
        self.vertex_y.clear()
        self.poly_id.clear()
        self.poly_text.clear()
        self.poly_lang.clear()


    

    def wheelEvent(self, event):
        """
        处理鼠标滚轮事件，用于缩放图像。

        :param event: 鼠标滚轮事件对象。
        """
        self.canvas.wheelEvent(event)
        self.scale_updated.emit(self.canvas.scale)


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

                if 'DataList' in data:
                    self.poly_data = []
                    self.poly_properties = []
                    self.poly_colors = []
                    for item in data['DataList']:
                        points = [QPoint(p[0], p[1]) for p in item['poly']]
                        self.poly_data.append(points)
                        self.poly_properties.append({
                            'id': item.get('id', len(self.poly_data)),
                            'text': item.get('text', ''),
                            'language': item.get('language', '')
                        })
                        self.poly_colors.append(Utils.generate_random_color())

                    
                    
                    self.update_poly_tree()
                    self.update_canvas_polygons()
                    self.canvas.poly_colors = self.poly_colors
                    if self.poly_tree.topLevelItemCount() > 0:
                        self.poly_tree.setCurrentItem(self.poly_tree.topLevelItem(0))
                    self.canvas.update()

            except Exception as e:
                self.status_updated.emit(f"加载标注失败: {str(e)}", "red")
    
    def update_poly_tree(self):
        """更新多边形列表，并设置对应颜色"""
        self.poly_tree.clear() # 清空树状控件中的所有项
        for i, prop in enumerate(self.poly_properties):
            # 创建树状控件的项，显示多边形的 ID、文本、顶点数和语言信息
            item = QTreeWidgetItem([
                str(prop['id']),
                prop['text'] ,
                " "+str(len(self.poly_data[i])),
                prop['language']
            ])

            color = self.poly_colors[i]

            for i in range(4):
                item.setForeground(i, color)

            self.poly_tree.addTopLevelItem(item)# 添加到树状控件中

            
    def on_tree_select(self):
        """处理列表选择事件"""
        selected_items = self.poly_tree.selectedItems()# 获取当前选中的项

        if selected_items:
            index = self.poly_tree.indexOfTopLevelItem(selected_items[0])
            self.selected_poly = index
            self.selected_vertex = -1
            
            if 0 <= index < len(self.poly_properties):
                prop = self.poly_properties[index]
                self.poly_id.setText(str(prop['id']))
                self.poly_text.setText(prop['text'])
                self.poly_lang.setText(prop['language'])
                
            self.canvas.selected_item = index
            self.canvas.update()
        else:
            self.selected_poly = -1
            self.selected_vertex = -1
            self.canvas.selected_item = -1
            self.canvas.update()
    

    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_C and self.creating_poly:
            self.cancel_create_poly()
        elif event.key() == Qt.Key_S:
            self.toggle_polygons_visibility()
        else:
            super().keyPressEvent(event)
        

    def on_canvas_click(self, event):
        """画布点击事件 - 包括多边形内部点击检测和拖动初始化"""

        x = (event.pos().x() - self.canvas.offset.x()) / self.canvas.scale
        y = (event.pos().y() - self.canvas.offset.y()) / self.canvas.scale
        click_point = QPointF(x, y)

        # 检查是否正在新建多边形
        if self.creating_poly and event.button() == Qt.LeftButton:
            # 添加多边形顶点，限制在图片范围内
            # 检查图片是否已加载且点击位置是否在图片范围内
            if self.canvas.image is not None:
                img_height, img_width = self.canvas.image.height(), self.canvas.image.width()

                if 0 <= click_point.x() < img_width and 0 <= click_point.y() < img_height:
                    
                    self.current_poly.append(click_point)
                   
                    self.update_canvas_polygons()
                    self.canvas.update()
                    self.status_updated.emit(f"已添加顶点 ({x}, {y})，继续点击添加或完成", "white")
                else:
                    # 在图片范围外，不添加顶点并提示
                    self.status_updated.emit("不能在图片范围外添加顶点，请在图片内点击", "red")
            else:
                # 没有加载图片，不添加顶点并提示
                self.status_updated.emit("请先加载图片", "red")
            return
        

        # # (旧)检查Q键是否按下，如果是则添加顶点
        # if self.shift_pressed and 0 <= self.selected_poly < len(self.poly_data):
        #     x = int((event.pos().x() - self.canvas.offset.x()) / self.canvas.scale)
        #     y = int((event.pos().y() - self.canvas.offset.y()) / self.canvas.scale)
        #     click_point = QPointF(x, y)
        #     # 设置一个阈值，判断点击是否在边上附近
        #     threshold = 10  # 5像素的阈值
        #     best_index = -1
        #     min_dist = float("inf")
        #     # 遍历多边形的边，找到距离最近的边
        #     for i in range(len(self.poly_data[self.selected_poly])):
        #         p1 = self.poly_data[self.selected_poly][i]
        #         p2 = self.poly_data[self.selected_poly][
        #             (i + 1) % len(self.poly_data[self.selected_poly])
        #         ]
        #         # 计算点到线段的距离
        #         dist = self.point_to_line_distance(
        #             click_point, QPointF(p1), QPointF(p2)
        #         )
        #         # 如果距离小于阈值且小于当前最小距离，则更新最佳位置
        #         if dist < threshold and dist < min_dist:
        #             min_dist = dist
        #             best_index = i + 1  # 插入到这条边之后
        #     # 如果找到了合适的边，添加新顶点
        #     if best_index != -1:
        #         # 在最佳位置插入新顶点
        #         self.poly_data[self.selected_poly].insert(
        #             best_index % len(self.poly_data[self.selected_poly]), QPoint(x, y)
        #         )
        #         # 更新界面
        #         self.update_canvas_polygons()
        #         self.canvas.update()
        #         self.update_poly_tree()
        #         self.status_updated.emit(f"已在多边形 {self.selected_poly} 的边上添加顶点", "white")
        #         return

        # 检查Shift键是否按下，如果是则添加顶点
        if self.shift_pressed and self.poly_data and event.button() == Qt.LeftButton:
            # 设置一个阈值，判断点击是否在边上附近
            # 阈值根据缩放比例动态调整

            threshold = 2/self.canvas.scale


            best_index = -1
            min_dist = float("inf")
            selected_poly = -1
            for i, poly in enumerate(self.poly_data):
                for j, point in enumerate(poly):
                    # 计算点到线段的距离
                    dist = self.point_to_line_distance(
                        click_point, QPointF(point), QPointF(poly[(j + 1) % len(poly)])
                    )
                    # 如果距离小于阈值且小于当前最小距离，则更新最佳位置
                    if dist < threshold and dist < min_dist:
                        min_dist = dist
                        best_index = j + 1  # 插入到这条边之后
                        selected_poly = i
           
            # 如果找到了合适的边，添加新顶点
            if best_index != -1:
                # 在最佳位置插入新顶点
                self.poly_data[selected_poly].insert(
                    best_index, click_point
                )

                self.update_poly_tree()

                self.vertex_idx.clear()
                self.vertex_x.clear()
                self.vertex_y.clear()

                prop = self.poly_properties[selected_poly]
                self.poly_id.setText(str(prop['id']))
                self.poly_text.setText(prop['text'])
                self.poly_lang.setText(prop['language'])

                self.poly_tree.setCurrentItem(self.poly_tree.topLevelItem(selected_poly))
                
                self.selected_poly = selected_poly
                self.selected_vertex = -1
                self.canvas.selected_item = selected_poly

                # 更新界面
                self.update_canvas_polygons()
                self.canvas.update()
                self.status_updated.emit(f"已在多边形 {self.selected_poly} 的边上添加顶点", "white")
                return
        


        # 检查是否点击了顶点
        if self.poly_data and event.button() == Qt.LeftButton:
            for i, poly in enumerate(self.poly_data):
                for j, point in enumerate(poly):
                    # 计算点击位置与顶点的距离
                    dist = ((point.x() - click_point.x()) **2 + (point.y() - click_point.y())** 2) **0.5 # 计算两点之间的直线距离，是基于数学中的欧几里得距离公式实现的。

                    if dist < 10 / self.canvas.scale:  # 考虑缩放的点击区域
                        self.vertex_idx.setText(str(j))
                        self.vertex_x.setText(str(point.x()))
                        self.vertex_y.setText(str(point.y()))
                        
                        prop = self.poly_properties[i]
                        self.poly_id.setText(str(prop['id']))
                        self.poly_text.setText(prop['text'])
                        self.poly_lang.setText(prop['language'])
                    
                        self.poly_tree.setCurrentItem(self.poly_tree.topLevelItem(i))
                        
                        self.dragging_vertex = True
                        self.selected_poly = i
                        self.selected_vertex = j                  
                        self.canvas.selected_item = i
                        self.canvas.update()
                        return
            
            for i, poly in enumerate(self.poly_data):
                polygon = [QPointF(p.x(), p.y()) for p in poly]
                q_poly = QPolygonF(polygon)
               
                if q_poly.containsPoint(click_point, Qt.OddEvenFill):
                    self.vertex_idx.clear()
                    self.vertex_x.clear()
                    self.vertex_y.clear()

                    prop = self.poly_properties[i]
                    self.poly_id.setText(str(prop['id']))
                    self.poly_text.setText(prop['text'])
                    self.poly_lang.setText(prop['language'])

                    self.poly_tree.setCurrentItem(self.poly_tree.topLevelItem(i))
                    
                    self.dragging_poly = True
                    self.selected_poly = i
                    self.selected_vertex = -1
                    self.canvas.selected_item = i

                    self.drag_start_pos = click_point# 记录拖动开始时的鼠标位置

                    self.poly_original_pos = [QPoint(p.x(), p.y()) for p in poly]# 保存多边形原始位置

                    self.canvas.update()
                    return
            
            self.selected_poly = -1
            self.selected_vertex = -1
            self.canvas.selected_item = -1
            self.canvas.update()

        self.original_mousePressEvent(event)


    def start_create_poly(self):
        """开始创建多边形"""
        self.creating_poly = True # 标记正在创建多边形
        self.canvas.setMouseTracking(True)

        self.current_poly = []# 清空当前正在创建的多边形顶点列表 
        self.status_updated.emit("请在图像上点击添加多边形顶点，完成后点击'完成多边形'", "white")

    def cancel_create_poly(self):
        """取消新建多边形"""
        if self.creating_poly:
            self.creating_poly = False
            self.current_poly = []
            self.update_canvas_polygons()
            self.canvas.update()
            self.canvas.setCursor(Qt.ArrowCursor)

            self.status_updated.emit("已取消新建多边形", "white")
            self.canvas.setMouseTracking(False)


    def finish_create_poly(self):
        """完成多边形创建"""
        if self.creating_poly and len(self.current_poly) >= 3:# 如果正在创建多边形且顶点数不少于 3 个，将当前多边形添加到多边形数据列表中
            self.poly_data.append(self.current_poly)
            self.poly_properties.append({
                'id': len(self.poly_data),
                'text': '',
                'language': ''
            })

            self.creating_poly = False
            self.current_poly = []
            self.canvas.setMouseTracking(False)


            self.update_poly_tree()
            self.update_canvas_polygons() # 根据显示状态设置画布的多边形数据

            self.vertex_idx.clear()
            self.vertex_x.clear()
            self.vertex_y.clear()

            index = len(self.poly_properties) - 1
            prop = self.poly_properties[index]
            self.poly_id.setText(str(prop['id']))
            self.poly_text.setText(prop['text'])
            self.poly_lang.setText(prop['language'])
            self.selected_poly = index
            self.selected_vertex = -1
            self.canvas.selected_item = index
            self.poly_tree.setCurrentItem(self.poly_tree.topLevelItem(index))
            self.canvas.poly_colors = self.poly_colors# 将多边形颜色列表赋值给画布的 poly_colors 属性
            self.canvas.update()
            
            self.status_updated.emit(f"已创建多边形，共 {len(self.poly_data)} 个", "white")

        elif len(self.current_poly) < 3:
            # 如果顶点数少于 3 个，弹出警告消息框
            QMessageBox.warning(self, "警告", "多边形至少需要3个顶点")

    def on_Key_ESCAPE_pressed(self):
        """取消新建多边形"""
        self.cancel_create_poly()
    
    def on_Key_N_pressed(self):
        """添加多边形"""
        if not self.creating_poly:
            self.canvas.setCursor(Qt.CrossCursor)   

            self.start_create_poly()
        else:
            
            self.canvas.setCursor(Qt.ArrowCursor)

            self.finish_create_poly()

    def on_Key_Left_pressed(self):
        """切换图片"""
        if self.file_pairs and self.current_index > 0:
            self.save_annotations()
            self.current_index -= 1
            self.load_current_file()

    def on_Key_Right_pressed(self):
        """切换图片"""
        if self.file_pairs and self.current_index < len(self.file_pairs) - 1:
            self.save_annotations()
            self.current_index += 1
            self.load_current_file()

    # 根据显示状态更新画布的多边形数据
    def update_canvas_polygons(self):
        """根据显示状态更新画布的多边形数据"""
        if self.show_polygons:
            # 如果显示多边形，使用实际数据
            if self.creating_poly and self.current_poly:
                self.canvas.polygons = self.poly_data + [self.current_poly]
            else:
                self.canvas.polygons = self.poly_data
        else:
            # 如果隐藏多边形，使用空列表
            self.canvas.polygons = []
            
    # 切换多边形显示/隐藏状态
    def toggle_polygons_visibility(self):
        """切换多边形的显示/隐藏状态"""
        self.show_polygons = not self.show_polygons
        self.update_canvas_polygons()
        self.canvas.update()
        
        if self.show_polygons:
            self.status_updated.emit("已显示多边形", "white")
        else:
            self.status_updated.emit("已隐藏多边形", "white")
            
    def delete_selected(self):
        """删除选中的多边形"""
        if 0 <= self.selected_poly < len(self.poly_data):
            del self.poly_data[self.selected_poly]
            del self.poly_properties[self.selected_poly]
            del self.poly_colors[self.selected_poly]
            del_index = self.selected_poly

            self.vertex_idx.clear()
            self.vertex_x.clear()
            self.vertex_y.clear()
            self.poly_id.clear()
            self.poly_text.clear()
            self.poly_lang.clear()

            self.update_poly_tree()
            self.update_canvas_polygons()

            if len(self.poly_data) > 0:

                index = del_index - 1
                if index < 0:
                    index = 0

                prop = self.poly_properties[index]
                self.poly_id.setText(str(prop['id']))
                self.poly_text.setText(prop['text'])
                self.poly_lang.setText(prop['language'])
                self.selected_poly = index
                self.selected_vertex = -1
                self.canvas.selected_item = index
                self.poly_tree.setCurrentItem(self.poly_tree.topLevelItem(index))
    
            self.canvas.update()
            # 更新状态标签的文本，显示剩余的多边形数量
            self.status_updated.emit(f"已删除选中多边形，剩余 {len(self.poly_data)} 个", "white")
            
    def clear_all(self):
        """清空所有多边形"""
        if self.poly_data:
            reply = QMessageBox.question(self, "确认", "确定要清空所有多边形吗？", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.init_vars()
                self.update_canvas_polygons()
                self.canvas.poly_colors = []
                self.canvas.update()
                self.update_poly_tree()
                self.poly_id.clear()
                self.poly_text.clear()
                self.poly_lang.clear()
                self.status_updated.emit("已清空所有多边形", "white")
    

    def delete_annotations(self):
        """删除标注"""
        if 0 <= self.current_index < len(self.file_pairs):
             
            reply = QMessageBox.question(self, "确认", "确定要删除当前图片和JSON文件吗？",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                file_pair = self.file_pairs[self.current_index]
                delete_path = os.path.join(os.path.dirname(file_pair['image']), 'deleted')
                if not os.path.exists(delete_path):
                    os.makedirs(delete_path)

                shutil.move(file_pair['json'], os.path.join(delete_path, os.path.basename(file_pair['json'])))
                shutil.move(file_pair['image'], os.path.join(delete_path, os.path.basename(file_pair['image'])))
                self.file_pairs.remove(file_pair)
                self.init_vars()

                self.current_index -= 1
                if self.current_index < 0:
                    self.current_index = 0


                self.load_current_file()

                self.status_updated.emit("已删除当前图像的标注","white")



    def save_annotations(self):
        """保存标注"""
        if 0 <= self.current_index < len(self.file_pairs):
            json_path = self.file_pairs[self.current_index]['json']
            data = {
                'FilePath': self.file_pairs[self.current_index]['image'].split('/')[-1],
                'DataList': []
            }
            
            for i, poly in enumerate(self.poly_data):
                prop = self.poly_properties[i]
                data['DataList'].append({
                    'id': prop['id'],
                    'text': prop['text'],
                    'poly': [[p.x(), p.y()] for p in poly],
                    'language': prop['language'],
                    "charsets": []
                })
            
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                self.status_updated.emit(f"标注已保存", "green")

            except Exception as e:
                self.status_updated.emit(f"保存标注失败: {str(e)}", "red")




    def go_to_image(self):
        """跳转图片"""
        index = int(self.go_text.text()) - 1
        if 0 <= index < len(self.file_pairs):
            self.current_index = index
            self.load_current_file()
            self.status_updated.emit(f"跳转至第 {index + 1} 张图片", "white")
        else:
            self.status_updated.emit("图片索引无效", "red")

    def reset_labels(self):
        """重置数据"""
        self.load_current_file()


    def reset_view(self):
        """重置视图"""
        self.canvas.reset_view()
        
    def update_poly_text(self):
        """更新多边形文本"""
        if 0 <= self.selected_poly < len(self.poly_properties):
            index = self.selected_poly

            self.poly_properties[self.selected_poly]['text'] = self.poly_text.text()
            self.update_poly_tree()
            self.selected_poly = index
            self.selected_vertex = -1
            self.canvas.selected_item = self.selected_poly
            self.poly_tree.setCurrentItem(self.poly_tree.topLevelItem(self.selected_poly))
            self.canvas.update()
            self.status_updated.emit("多边形文本已更新", "white")

    def update_poly_language(self):
        """更新多边形语言"""
        if 0 <= self.selected_poly < len(self.poly_properties):
            index = self.selected_poly
            self.poly_properties[self.selected_poly]['language'] = self.poly_lang.text()
            self.update_poly_tree()
            self.selected_poly = index
            self.selected_vertex = -1
            self.canvas.selected_item = self.selected_poly
            self.poly_tree.setCurrentItem(self.poly_tree.topLevelItem(self.selected_poly))
            self.canvas.update()
            # 更新状态标签的文本，显示多边形语言已更新
            self.status_updated.emit("多边形语言已更新", "white")

    def apply_vertex_coords(self):
        """应用顶点坐标修改"""
        if 0 <= self.selected_poly < len(self.poly_data) and 0 <= self.selected_vertex < len(self.poly_data[self.selected_poly]):
            try:
                x = int(self.vertex_x.text())
                y = int(self.vertex_y.text())
                self.poly_data[self.selected_poly][self.selected_vertex] = QPoint(x, y)
                self.update_canvas_polygons()
                self.canvas.update()
                self.status_updated.emit("顶点坐标已更新", "white")

            except ValueError:
                self.status_updated.emit("顶点坐标必须是整数", "red")
                
    def on_d_pressed(self):
        """删除顶点"""
        if 0 <= self.selected_poly < len(self.poly_data) and 0 <= self.selected_vertex < len(self.poly_data[self.selected_poly]):
            if len(self.poly_data[self.selected_poly]) > 3:
                del self.poly_data[self.selected_poly][self.selected_vertex]
                self.selected_vertex = -1
                self.vertex_idx.clear()
                self.vertex_x.clear()
                self.vertex_y.clear()
                self.update_canvas_polygons()
                self.canvas.update()
                self.update_poly_tree()
                self.status_updated.emit("已删除顶点", "white")
            else:
                QMessageBox.warning(self, "警告", "多边形至少需要3个顶点")

    def on_shift_pressed(self, pressed):

        self.shift_pressed = pressed
        if pressed:
            self.status_updated.emit("Shift键已按下，点击多边形添加顶点", "white")
        else:
            self.status_updated.emit("Shift键已释放", "white")

    
    def point_to_line_distance(self, point, line_p1, line_p2):
        """计算点到线段的距离"""     
        # 检查线段段的两个点是否重合（长度为0）
        if line_p1 == line_p2:
            # 如果两个点重合，直接返回点到该点的距离
            dx = point.x() - line_p1.x()
            dy = point.y() - line_p1.y()
            return (dx**2 + dy**2) **0.5

        line_vec = line_p2 - line_p1 # 线段的向量        
        point_vec = point - line_p1 # 点到线段起点的向量        
        line_len_sq = line_vec.x()**2 + line_vec.y()** 2 # 线段长度的平方  
        t = max(0, min(1, (point_vec.x() * line_vec.x() + point_vec.y() * line_vec.y()) / line_len_sq)) # 计算投影比例
        projection = line_p1 + t * line_vec# 投影点
        
        # 计算点到投影点的距离
        dx = point.x() - projection.x()
        dy = point.y() - projection.y()
        
        return (dx**2 + dy**2) **0.5
            

    def on_canvas_drag(self, event):
        """画布拖动事件 - 多边形整体拖动功能（优化边界检查）"""

        # 计算拖动位置在图像坐标系下的坐标
        x = (event.pos().x() - self.canvas.offset.x()) / self.canvas.scale
        y = (event.pos().y() - self.canvas.offset.y()) / self.canvas.scale
        click_point = QPointF(x, y)

        has_image = self.canvas.image is not None
        if has_image :
            img_width = self.canvas.image.width()
            img_height = self.canvas.image.height()
            max_x = img_width - 1 
            max_y = img_height - 1 
        else:
            return

        if self.dragging_vertex and 0 <= self.selected_poly < len(self.poly_data) and 0 <= self.selected_vertex < len(self.poly_data[self.selected_poly]) :
            
            if not self.show_polygons:
                return
            
            x_clamped = max(0, min(click_point.x(), max_x))
            y_clamped = max(0, min(click_point.y(), max_y))
            
            self.poly_data[self.selected_poly][self.selected_vertex] = QPoint(x_clamped, y_clamped)# 更新多边形数据

            self.vertex_x.setText(str(int(x_clamped)))
            self.vertex_y.setText(str(int(y_clamped)))
            self.update_canvas_polygons()
            self.canvas.update()
            return
        

        if self.dragging_poly and 0 <= self.selected_poly < len(self.poly_data):# 拖动多边形


            if not self.show_polygons:
                return 
        
            dx = click_point.x() - self.drag_start_pos.x()
            dy = click_point.y() - self.drag_start_pos.y()
            
            new_poly = []
            for point in self.poly_original_pos:
                # 计算新坐标
                new_x = point.x() + dx
                new_y = point.y() + dy
                
                # 限制新坐标在图像范围内（四舍五入为整数）
                new_x_clamped = max(0, min(round(new_x), max_x))
                new_y_clamped = max(0, min(round(new_y), max_y))
                
                new_poly.append(QPoint(new_x_clamped, new_y_clamped))
            
            # 更新多边形数据（确保顶点数量不变）
            self.poly_data[self.selected_poly] = new_poly
            self.update_canvas_polygons()
            self.canvas.update()
            return
        
        if self.creating_poly:
            original_poly = self.current_poly.copy()
            self.current_poly.append(click_point)
            self.update_canvas_polygons()
            self.canvas.update()
            self.current_poly = original_poly
            return


        self.original_mouseMoveEvent(event)

    def on_canvas_release(self, event):
        """画布释放事件 - 新增结束多边形拖动的处理"""
        if event.button() == Qt.LeftButton:
            if self.dragging_vertex: # 拖动顶点
                self.dragging_vertex = False
            elif self.dragging_poly: # 拖动多边形
                self.dragging_poly = False
        else:
            self.original_mouseReleaseEvent(event)    
    
    def closeEvent(self, event):
        """父窗口关闭时，主动清理树控件"""
        self.poly_tree.cleanup()  # 手动触发清理
        super().closeEvent(event)  # 调用父类关闭事件

    def show_shortcut_help(self):
        """显示带样式的快捷键说明弹窗"""
        # 创建自定义对话框而非普通QMessageBox，以便更好地控制样式
        
        
        class ShortcutDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("快捷键说明")
                self.setMinimumSize(600, 400)
                base_dir = os.path.dirname(os.path.abspath(__file__))
                self.setWindowIcon(QIcon(os.path.join(base_dir, "images","help.png")))
                self.setModal(True)
                
                # 设置整体样式
                self.setStyleSheet("""
                    QDialog {
                        background-color: #f5f5f5;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                                   
                    QTextBrowser {
                        background-color: white;
                        border: 1px solid #ddd;
                        border-radius: 6px;
                        padding: 15px;
                        font-size: 14px;
                        line-height: 1.6;
                    }
                                   
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-size: 14px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QPushButton:pressed {
                        background-color: #3d8b40;
                    }
                """)
                
                layout = QVBoxLayout(self)
                
                # 创建文本浏览器用于显示格式化的快捷键内容
                text_browser = QTextBrowser()
                
                # 设置快捷键说明内容（带HTML样式）
                shortcut_content = """
                <style>
                    h3 {
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 8px;
                        margin-top: 20px;
                        margin-bottom: 15px;
                    }
                    ul {
                        color: #2c3e50;
                        margin: 10px 0;
                        padding-left: 25px;
                    }
                    li {
                        margin: 8px 0;
                    }
                    b {
                        color: #e74c3c;
                    }
                    .section-title {
                        color: #3498db;
                        font-size: 16px;
                    }
                </style>
                
                <h3>一、基础操作快捷键</h3>
                <ul>
                    <li><b>N键开始</b>：新建多边形</li>
                    <li><b>N键结束</b>：完成多边形</li>
                    <li><b>ESC键</b>：取消新建多边形</li>
                    <li><b>DEL键</b>：删除选中多边形</li>
                    <li><b>CTRL键+S键</b>：保存当前标注</li>
                    <li><b>S键</b>：切换多边形显示/隐藏</li>
                    <li><b>SPACE键</b>：重置视图（居中显示）</li>
                    <li><b>SHIFT键（长按）</b>：添加顶点（点击多边形边缘）</li>
                    <li><b>D键</b>：删除选中顶点（需先选中顶点）</li>
                    <li><b>LEFT键</b>：切换到上一张图片（自动保存当前标注）</li>

                    <li><b>RIGHT键</b>：切换到下一张图片（自动保存当前标注）</li>
                </ul>
                
                <h3>二、鼠标操作</h3>
                <ul>
                    <li><b>左键点击</b>：
                        <ul>
                            <li>新建多边形时：添加顶点</li>
                            <li>选中顶点时：拖动调整顶点位置</li>
                            <li>选中多边形内部：拖动整个多边形</li>
                        </ul>
                    </li>
                    <li><b>右键拖动</b>：平移画布</li>
                    <li><b>鼠标滚轮</b>：缩放画布</li>
                </ul>
                
                <h3>三、列表操作</h3>
                <ul>
                    <li><b>Tab键</b>：切换选中多边形列表项</li>
                </ul>
                """
                text_browser.setHtml(shortcut_content)
                
                # 添加关闭按钮
                close_btn = QPushButton("关闭")
                close_btn.clicked.connect(self.accept)
                
                # 添加到布局
                layout.addWidget(text_browser)
                layout.addWidget(close_btn, alignment=Qt.AlignRight | Qt.AlignBottom)
    
        # 显示对话框
        dialog = ShortcutDialog(self)
        dialog.exec_()


class TabNavigationTreeWidget(QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        # 基础设置
        self.setFocusPolicy(Qt.NoFocus)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setTabKeyNavigation(False)  # 禁用默认Tab导航
        

       # 安装事件过滤器
        QApplication.instance().installEventFilter(self)

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Tab:
          
            current_item = self.currentItem()
            if not current_item:
                return super().keyPressEvent(event)
                
            current_col = self.currentColumn()
            row_count = self.topLevelItemCount()
            current_row = self.indexOfTopLevelItem(current_item)
            if current_row == -1:
                return super().keyPressEvent(event)
            
            # # 处理Tab和Shift+Tab
            # if event.modifiers() & Qt.ShiftModifier:
            #     next_row = current_row - 1 if current_row > 0 else row_count - 1
            # else:

            next_row = current_row + 1 if current_row < row_count - 1 else 0
            
            next_item = self.topLevelItem(next_row)
            if next_item:
                self.setCurrentItem(next_item, current_col)
                # 处理后让控件获取焦点，提升用户体验
                #self.setFocus()
            event.accept()
            return
        super().keyPressEvent(event)
    
    def eventFilter(self, obj, event):
        """事件过滤器：捕获全局Tab键事件"""
        # 只处理键盘按下事件
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            
            # 检查是否有顶级项目（避免空列表时处理）
            if self.topLevelItemCount() > 0:

                # 直接调用自己的按键处理方法
                self.keyPressEvent(event)
                return True  # 拦截事件，不再传递
        return super().eventFilter(obj, event)



class CustomTreeDelegate(QStyledItemDelegate):
    """修复颜色验证的自定义代理类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree = parent  # 保存树控件引用

    def paint(self, painter, option, index):
        # 获取树控件
        tree = self.parent()
        if not tree:
            super().paint(painter, option, index)
            return
            
        item = tree.topLevelItem(index.row())#获取当前行的项

        if not item:
            super().paint(painter, option, index)
            return
            
        original_option = option# 保存原始选项
        
        option = QStyleOptionViewItem(original_option)# 创建选项副本，避免修改原始对象
        
        is_selected = tree.selectionModel().isSelected(index)# 检查项是否被选中
        
        brush = item.foreground(index.column())# 获取项的前景色（QBrush）
        
        # 正确检查颜色是否有效的方式：获取画笔的颜色并检查是否有效
        text_color = brush.color()  # 从QBrush中获取QColor对象
        has_valid_color = text_color.isValid() and text_color.alpha() > 0
        
        # 应用我们的颜色设置
        if has_valid_color:
            # 设置文本颜色
            palette = option.palette
            palette.setColor(QPalette.Text, text_color)
            option.palette = palette
        
        # 如果项被选中，绘制自定义选中效果
        if is_selected:
            # 绘制选中背景
            # custom_bg_color = QColor(255, 255, 0)  # 浅蓝

            painter.fillRect(option.rect, option.palette.highlight())

            # 确保文本颜色可见
            if has_valid_color:
                palette.setColor(QPalette.HighlightedText, text_color)
                option.palette = palette
            # 清除选中状态标志，避免默认绘制覆盖我们的设置
            option.state &= ~QStyle.State_Selected
        
        # 调用基类方法进行绘制
        super().paint(painter, option, index)







