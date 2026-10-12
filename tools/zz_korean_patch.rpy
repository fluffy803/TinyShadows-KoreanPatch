# 小小的身影，重叠的内心 — 한국어 패치
#
# 원본 *.rpa 는 건드리지 않는다. 이 파일과 tl/korean/, 그리고 언어 표시 이미지만
# game/ 에 얹으면 동작한다.
#
# 설정 화면의 이미지·텍스트 언어 선택에 "한국어"가 추가된다.
#   텍스트·이미지: 简体中文 → 日本語 → 한국어 (좌우 화살표로 순환)
#   음성: 원본 그대로 (중국어 / 일본어), 첫 실행 시 일본어

init offset = 10

default persistent._ko_initialized = False

image sys_data_bo5_korean_confim:
    "gui/custom/system/setting/sys_data_bo5_korean_confim.png"


init python:

    _KO_LANG_CYCLE = [None, "japanese", "korean"]
    _KO_VOICE_CYCLE = [None, "japanese"]

    def _ko_get_language(category):
        if category in (None, "all"):
            return _preferences.text_language
        return getattr(_preferences, category + "_language", None)

    def _ko_set_language(category, language):
        if category == "text":
            renpy.translation.change_text_language(language)
        elif category == "image":
            renpy.translation.change_image_language(language)
        elif category == "voice":
            renpy.translation.change_voice_language(language)

    class ToggleLanguage(Action):
        """
        원본 ToggleLanguage(중국어 <-> 일본어 2개 토글)를 한국어까지 3개 순환으로 바꾼다.
        음성은 한국어 더빙이 없으므로 원래대로 2개만 순환한다.
        """

        def __init__(self, category=None, step=1):
            self.category = category
            self.step = step

        def _next(self, category):
            cycle = _KO_VOICE_CYCLE if category == "voice" else _KO_LANG_CYCLE
            current = _ko_get_language(category)
            i = cycle.index(current) if current in cycle else 0
            return cycle[(i + self.step) % len(cycle)]

        def __call__(self):
            if self.category in (None, "all"):
                target = self._next("text")
                _ko_set_language("text", target)
                _ko_set_language("image", target)
                _ko_set_language("voice", target if target in _KO_VOICE_CYCLE else None)
            else:
                _ko_set_language(self.category, self._next(self.category))
            renpy.restart_interaction()

        def get_selected(self):
            return False

    # 첫 실행 때만 텍스트·이미지를 한국어로, 음성을 일본어로(번역 기준이 일본어판).
    # 이후엔 플레이어가 고른 언어를 따른다.
    def _ko_startup():
        if persistent._ko_initialized:
            return
        persistent._ko_initialized = True
        if _preferences.text_language != "korean":
            renpy.translation.change_text_language("korean")
        if _preferences.image_language != "korean":
            renpy.translation.change_image_language("korean")
        if _preferences.voice_language != "japanese":
            renpy.translation.change_voice_language("japanese")

    config.interact_callbacks.append(_ko_startup)


screen language_selector(base_y, category=None):

    $ _ko_cur = _ko_get_language(category)

    imagebutton:
        idle "gui/custom/system/setting/sys_data_lang_bo_left_normal.png"
        hover "gui/custom/system/setting/sys_data_lang_bo_left_click.png"
        activate_sound persistent.button_activate_sound
        hover_sound persistent.button_hover_sound
        xpos 1446
        ypos base_y + 23
        action ToggleLanguage(category, -1)

    if _ko_cur == "japanese":
        add "sys_data_bo5_japan_confim":
            xpos 1492
            ypos base_y
    elif _ko_cur == "korean":
        add "sys_data_bo5_korean_confim":
            xpos 1492
            ypos base_y
    else:
        add "sys_data_bo5_sc_confim":
            xpos 1492
            ypos base_y

    imagebutton:
        idle "gui/custom/system/setting/sys_data_lang_bo_right_normal.png"
        hover "gui/custom/system/setting/sys_data_lang_bo_right_click.png"
        activate_sound persistent.button_activate_sound
        hover_sound persistent.button_hover_sound
        xpos 1740
        ypos base_y + 23
        action ToggleLanguage(category, 1)


# 한국어는 음절 중간이 아니라 띄어쓰기에서 줄을 바꾼다.
translate korean style default:
    language "korean-with-spaces"
