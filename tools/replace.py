import json


class Replace:

    def __init__(self, picture_font_path, icon_font_path):
        self.picture_font_path = picture_font_path
        self.icon_font_path = icon_font_path

    def picture_font_reverse(self, ids):
        with open(self.picture_font_path, 'r', encoding='UTF-8') as file:
            json_data = json.load(file)['texts']
        if ids in json_data:
            return json_data[ids]
        else:
            return f"[{ids}]"

    def icon_font_reverse(self, ids):
        with open(self.icon_font_path, 'r', encoding='UTF-8') as file:
            json_data = json.load(file)['texts']
        if ids in json_data:
            return json_data[ids]
        else:
            return f"[{ids}]"
