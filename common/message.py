from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import Qt, QObject

from QtUniversalToolFrameWork.components.widgets.info_bar import InfoBar, InfoBarPosition
from QtUniversalToolFrameWork.components.dialog_box.message_box import MessageBox

class Message(QObject):

    DURATION = 2000

    def __init__(self, parent=None):

        super().__init__(parent)

        #self._validate_point_message_box = MessageBox("错误", "标注点坐标加载异常！",parent)


    def _get_valid_parent(self):
        app = QApplication.instance()
        if not app:
            return QDesktopWidget()
        
        main_win = app.activeWindow()
        if main_win and main_win.isVisible():
            return main_win
        
        top_wins = app.topLevelWidgets()
        for win in top_wins:
            if win.isVisible():
                return win
        
        return QDesktopWidget()

    def show_info_message(self, title: str, content: str):
        InfoBar.info(
            title=title, content=content, orient=Qt.Horizontal,
            isClosable=True, duration=self.DURATION, position=InfoBarPosition.TOP_RIGHT,
            parent=self._get_valid_parent()) 

    def show_error_message(self, title: str, content: str):
        InfoBar.error(
            title=title, content=content, orient=Qt.Horizontal,
            isClosable=True,duration=self.DURATION, position=InfoBarPosition.TOP_RIGHT,
            parent=self._get_valid_parent())

    def show_success_message(self, title: str, content: str):
        InfoBar.success(
            title=title, content=content, orient=Qt.Horizontal,
            isClosable=True, duration=self.DURATION, position=InfoBarPosition.TOP_RIGHT,
            parent=self._get_valid_parent())

    def show_message_dialog(self, title: str, content: str):
        
        w = MessageBox(title, content, self._get_valid_parent())
        w.setContentCopyable(True)
        w.exec() 

message = Message()