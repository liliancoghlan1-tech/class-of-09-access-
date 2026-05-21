## Class of '09 — NVDA Accessibility Mod
##
## Reads focused menu items and dialog choices aloud through NVDA.
## Story dialogue is intentionally excluded — it is already voice-acted.
##
## Files installed:
##   game\accessibility_nvda.rpy       (this file)
##   nvdaControllerClient64.dll        (placed in the same folder as the .exe)
##
## Requires NVDA screen reader to be running. No other configuration needed.


## ── Navigation screen override ────────────────────────────────────────────
## The compiled navigation() screen uses imagebutton displayables that have
## no text, so _tts_all() returns empty and NVDA has nothing to speak.
## All five buttons sit at xpos 0 / ypos 0 (full-screen overlapping images
## masked by focus_mask files), so Ren'Py's spatial arrow-key focus system
## cannot determine which button is above or below another.
##
## Fix: define per-button styles with unique focus_rect values.  focus_rect
## is not accepted as a direct imagebutton keyword (parse error), but it IS
## valid inside a style definition.  The styles inherit from navigation_button
## so all other visual/layout properties are preserved.
##
## This definition runs at init priority 0 > compiled screens.rpyc (-1).

style a11y_nav_1 is navigation_button:
    focus_rect (0, 100, 600, 100)

style a11y_nav_2 is navigation_button:
    focus_rect (0, 250, 600, 100)

style a11y_nav_3 is navigation_button:
    focus_rect (0, 400, 600, 100)

style a11y_nav_4 is navigation_button:
    focus_rect (0, 550, 600, 100)

style a11y_nav_5 is navigation_button:
    focus_rect (0, 700, 600, 100)


screen navigation():
    style_prefix "navigation"

    imagebutton:
        style "a11y_nav_1"
        idle "NEWGAME.png"
        hover "NEWGAME_selected.png"
        xpos 0
        ypos 0
        focus_mask "NEWGAME_mask.png"
        activate_sound "audio/MainMenuPress.mp3"
        hover_sound "audio/MainMenuRollover.mp3"
        action Start()
        alt "New Game"

    imagebutton:
        style "a11y_nav_2"
        idle "CONTINUE.png"
        hover "CONTINUE_selected.png"
        xpos 0
        ypos 0
        focus_mask "CONTINUE_mask.png"
        activate_sound "audio/MainMenuPress.mp3"
        hover_sound "audio/MainMenuRollover.mp3"
        action ShowMenu("load")
        alt "Continue"

    imagebutton:
        style "a11y_nav_3"
        idle "OPTIONS.png"
        hover "OPTIONS_selected.png"
        xpos 0
        ypos 0
        focus_mask "OPTIONS_mask.png"
        activate_sound "audio/MainMenuPress.mp3"
        hover_sound "audio/MainMenuRollover.mp3"
        action ShowMenu("preferences")
        alt "Options"

    imagebutton:
        style "a11y_nav_4"
        idle "ABOUT.png"
        hover "ABOUT_selected.png"
        xpos 0
        ypos 0
        focus_mask "ABOUT_mask.png"
        activate_sound "audio/MainMenuPress.mp3"
        hover_sound "audio/MainMenuRollover.mp3"
        action ShowMenu("about")
        alt "About"

    imagebutton:
        style "a11y_nav_5"
        idle "EXIT.png"
        hover "EXIT_selected.png"
        xpos 0
        ypos 0
        focus_mask "EXIT_mask.png"
        activate_sound "audio/MainMenuPress.mp3"
        hover_sound "audio/MainMenuRollover.mp3"
        action Quit()
        alt "Exit"


init 999 python:
    import ctypes
    import os

    ## ── Load NVDA Controller Client ────────────────────────────────────────
    _a11y_nvda = None

    for _a11y_dll_name in ["nvdaControllerClient64.dll", "nvdaControllerClient32.dll"]:
        _a11y_dll_path = os.path.join(renpy.config.basedir, _a11y_dll_name)
        try:
            _a11y_nvda = ctypes.windll.LoadLibrary(_a11y_dll_path)
            _a11y_nvda.nvdaController_speakText.argtypes  = [ctypes.c_wchar_p]
            _a11y_nvda.nvdaController_speakText.restype   = ctypes.c_uint
            _a11y_nvda.nvdaController_cancelSpeech.restype = ctypes.c_uint
            break
        except (OSError, AttributeError):
            _a11y_nvda = None

    def _a11y_speak(text):
        if not _a11y_nvda:
            return
        if not isinstance(text, unicode):
            try:
                text = text.decode("utf-8", "replace")
            except Exception:
                return
        text = text.strip()
        if not text:
            return
        try:
            _a11y_nvda.nvdaController_cancelSpeech()
            _a11y_nvda.nvdaController_speakText(text)
        except Exception:
            pass

    ## ── Story-dialogue guard ───────────────────────────────────────────────
    ## Returns True when it is appropriate to speak button labels:
    ## always at menus, never during plain story dialogue (say/nvl without
    ## an accompanying choice screen).

    def _a11y_on_menu():
        try:
            if renpy.get_screen("choice") is not None:
                return True
            if renpy.get_screen("say") is not None:
                return False
            if renpy.get_screen("nvl") is not None:
                return False
        except Exception:
            pass
        return True

    ## ── Button focus hook ──────────────────────────────────────────────────
    ## Intercepts Ren'Py's Button.focus() to speak the button's label via
    ## NVDA.  If a new unknown screen just appeared (see watcher below), the
    ## screen's full TTS text is spoken first so the user gets context before
    ## hearing which button was auto-focused.

    import renpy.display.behavior as _a11y_beh

    _a11y_orig_focus    = _a11y_beh.Button.focus
    _a11y_last_text     = [u""]
    _a11y_pending_ctx   = [u""]   # screen context to prepend on next button focus

    def _a11y_btn_focus(self, default=False):
        _a11y_orig_focus(self, default)

        if not _a11y_on_menu():
            return

        try:
            btn_text = self._tts_all()
        except Exception:
            return

        if not isinstance(btn_text, unicode):
            try:
                btn_text = btn_text.decode("utf-8", "replace")
            except Exception:
                return
        btn_text = btn_text.strip()

        ## If there is pending screen context (set by the watcher when a new
        ## unknown screen appeared), use it as the full speech so the user
        ## hears the screen's text together with the focused button label.
        ## The pending context already includes the button labels from
        ## _tts_all() on the screen, so we use it as-is to avoid repetition.
        if _a11y_pending_ctx[0]:
            full_text = _a11y_pending_ctx[0]
            _a11y_pending_ctx[0] = u""
        else:
            full_text = btn_text

        if not full_text or full_text == _a11y_last_text[0]:
            return

        _a11y_last_text[0] = full_text
        _a11y_speak(full_text)

    _a11y_beh.Button.focus = _a11y_btn_focus

    ## ── Menu transition watcher ────────────────────────────────────────────
    ## Called at the start of every interact() cycle. Responsibilities:
    ##
    ##   1. Initial keyboard focus.  Posts a K_DOWN keydown so that arrow-key
    ##      navigation is available from the first frame (no mouse click
    ##      required). K_DOWN is used instead of K_TAB because Tab toggles
    ##      dialogue-skip mode in this game. The repeat=0 field is required
    ##      by pygame_sdl2 / pygame 2 — without it map_event() raises
    ##      AttributeError: 'EventType' has no attribute 'repeat'.
    ##
    ##   2. Narrator-menu captions.  When a menu: statement has a caption,
    ##      Ren'Py shows say + choice simultaneously.  That combination never
    ##      occurs during plain story, so it reliably identifies a captioned
    ##      menu.  We read the say text once.
    ##
    ##   3. Unknown overlay screens.  The post-ending phone/message screen
    ##      (and similar custom screens) are not choice, say, or nvl screens.
    ##      When one appears while in menu state, we capture its full TTS text
    ##      as pending context so the button-focus hook can speak it together
    ##      with the first focused button label.

    ## Screen names we handle explicitly elsewhere — do not read their TTS
    ## as "unknown screen context".
    _A11Y_KNOWN = frozenset({
        "main_menu", "navigation", "game_menu", "say", "nvl", "choice",
        "save", "load", "preferences", "help", "about",
        "actors", "artists", "aboutmenu", "quick_menu", "skip_indicator",
        "notify", "pause_save", "pause_prefs", "file_slots",
        "pause_file_slots", "nvl_dialogue", "keyboard_help", "mouse_help",
        "gamepad_help",
    })

    _a11y_prev_on_menu       = [False]
    _a11y_choice_was_visible = [False]
    _a11y_caption_spoken     = [u""]
    _a11y_prev_screens       = [frozenset()]

    def _a11y_post_down():
        try:
            import pygame
            pygame.event.post(pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_DOWN, mod=0, unicode=u"", scancode=0, repeat=0
            ))
        except Exception:
            pass

    def _a11y_screen_text(screen_name):
        try:
            sd = renpy.get_screen(screen_name)
            if sd is None:
                return u""
            t = sd._tts_all()
            if not isinstance(t, unicode):
                t = t.decode("utf-8", "replace")
            return t.strip()
        except Exception:
            return u""

    def _a11y_visible_screens():
        result = set()
        try:
            for k in renpy.display.screen.screens:
                name = k[0] if isinstance(k, tuple) else str(k)
                result.add(name)
        except Exception:
            pass
        return frozenset(result)

    def _a11y_menu_watcher():
        try:
            on_menu    = _a11y_on_menu()
            has_choice = renpy.get_screen("choice") is not None
            has_say    = renpy.get_screen("say")    is not None

            should_post_down = False

            ## 1. Entering menu state for the first time → establish focus.
            if on_menu and not _a11y_prev_on_menu[0]:
                should_post_down = True

            ## 2. Choice + say visible together → narrator-menu caption.
            if has_choice and has_say and not _a11y_choice_was_visible[0]:
                cap = _a11y_screen_text("say")
                if cap and cap != _a11y_caption_spoken[0]:
                    _a11y_caption_spoken[0] = cap
                    _a11y_speak(cap)

            ## 3. New unknown screen appeared while in menu state.
            if on_menu:
                current = _a11y_visible_screens()
                new     = current - _a11y_prev_screens[0]
                for name in sorted(new):          # sorted for determinism
                    if name not in _A11Y_KNOWN:
                        text = _a11y_screen_text(name)
                        if text:
                            _a11y_pending_ctx[0] = text
                            should_post_down = True
                            break
                _a11y_prev_screens[0] = current
            else:
                _a11y_prev_screens[0] = _a11y_visible_screens()

            if should_post_down:
                _a11y_post_down()

            _a11y_prev_on_menu[0]       = on_menu
            _a11y_choice_was_visible[0] = has_choice
        except Exception:
            pass

    _a11y_cb_list = getattr(renpy.config, "interact_callbacks", None)
    if _a11y_cb_list is None:
        renpy.config.interact_callbacks = []
        _a11y_cb_list = renpy.config.interact_callbacks
    _a11y_cb_list.append(_a11y_menu_watcher)
