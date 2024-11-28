from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.lang import Builder
from datetime import date
import os

class DialogMixin():
    def show_result_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="Copy",
                    on_release=lambda *args: Clipboard.copy(text)),
                
                MDFlatButton(
                    text="OK",
                    on_release=lambda *args: dialog.dismiss()
                )
            ]
        )
        dialog.open()   
        
    def show_error_dialog(self, text):
            dialog = MDDialog(
                title="Error",
                text=text,
                buttons=[
                    MDFlatButton(
                        text="OK",
                        on_release=lambda *args: dialog.dismiss()
                    )
                ]
            )
            dialog.open()     
 
class Calculations:
    @staticmethod
    def calculate_bbls(dip):
        return abs(int(((dip * 5.66) - 550) * 2))
    
    def calculate_inches(bbl):
        singleTank = int(bbl/2)
        return abs(int((550 - singleTank)/5.66))

class InputValidator:
    @staticmethod
    def validate_dip(dip, min_val, max_val):
        try:
            dip_value = int(dip)
            if dip_value < min_val or dip_value > max_val:
                return False, f"Must be between {min_val} and {max_val}"
            return True, None
        except ValueError:
            return False, "Please enter a valid number"

class MainMenuScreen(MDScreen):
    def toggle_theme(self):
        app = MDApp.get_running_app()
        
        if app.theme_cls.theme_style == "Dark":
            app.theme_cls.theme_style = "Light"
        else: 
            app.theme_cls.theme_style = "Dark"
                   
class ToBBLScreen(MDScreen, DialogMixin):  
    def calculate_volume(self):
        dip = self.ids.dip_input.text
        is_valid, error_msg = InputValidator.validate_dip(dip, min_val=0 , max_val= 97)
        
        if not is_valid:
            self.show_error_dialog(error_msg)
            return
            
        volume = Calculations.calculate_bbls(int(dip))
        result = f"{volume}bbl"
        self.show_result_dialog("Current Volume", result)

class ToInchesScreen(MDScreen, DialogMixin):
    def convert_to_inches(self):
        bbl = self.ids.barrel_input.text
        
        is_valid, error_msg = InputValidator.validate_dip(bbl, min_val=1, max_val=1100)
        
        if not is_valid:
            self.show_error_dialog(error_msg)
            return
            
        inch = Calculations.calculate_inches(int(bbl))
        result = f'{inch} Inch'
        self.show_result_dialog("Current Dip" ,result)

class GenerateReportScreen(MDScreen, DialogMixin):  
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.first_time = "am"
        self.last_time = "pm"
        self.which_shift = "Day"
        self.is_filled = False
          
    def select_shift(self, shift_type):
        if shift_type == 'day':
            self.first_time = "am"
            self.last_time = "pm"
            self.which_shift = "Day"
        else:
            self.first_time = "pm"
            self.last_time = "am"
            self.which_shift = "Night"

    def toggle_filled(self, is_filled):
        self.is_filled = is_filled
        
        if self.is_filled:
            self.ids.fill_fields.height = 80
            self.ids.fill_fields.opacity = 1
            self.ids.before_fill.disabled = False
            self.ids.after_fill.disabled = False 
                  
        else:
            self.ids.fill_fields.height = 0
            self.ids.fill_fields.opacity = 0
            self.ids.before_fill.disabled = True
            self.ids.after_fill.disabled = True

    def validate_report_inputs(self):
        first_dip_input = self.ids.first_dip.text
        first_dip_valid, first_dip_error = InputValidator.validate_dip(
            first_dip_input, min_val=0, max_val=97
        )
        if not first_dip_valid:
            self.show_error_dialog(f"First Dip: {first_dip_error}")
            return False
        
        last_dip_input = self.ids.last_dip.text
        last_dip_valid, last_dip_error = InputValidator.validate_dip(
            last_dip_input, min_val=0, max_val=97
        )
        if not last_dip_valid:
            self.show_error_dialog(f"Last Dip: {last_dip_error}")
            return False    
    
        if self.is_filled:
            before_fill_input = self.ids.before_fill.text
            before_fill_valid, before_fill_error = InputValidator.validate_dip(
                before_fill_input, min_val=0, max_val=97
            )
            if not before_fill_valid:
                self.show_error_dialog(f"Before Fill Dip: {before_fill_error}")
                return False

            after_fill_input = self.ids.after_fill.text
            after_fill_valid, after_fill_error = InputValidator.validate_dip(
                after_fill_input, min_val=0, max_val=97
            )
            if not after_fill_valid:
                self.show_error_dialog(f"After Fill Dip: {after_fill_error}")
                return False

        return True
    
    def generate_report(self):
        # Validate input first
        if not self.validate_report_inputs():
            return
        
        # Convert inputs to integers
        first_dip = int(self.ids.first_dip.text)
        last_dip = int(self.ids.last_dip.text)
            
        # Calculate volumes 
        first_vol = Calculations.calculate_bbls(first_dip)
        last_vol = Calculations.calculate_bbls(last_dip)
                
        if self.is_filled:
            # Validate additional fields for filled scenario
            before_fill = int(self.ids.before_fill.text)
            after_fill = int(self.ids.after_fill.text)
                
            before_fill_vol = Calculations.calculate_bbls(before_fill)
            after_fill_vol = Calculations.calculate_bbls(after_fill)
                
            total_consum = (first_vol - before_fill_vol) + (after_fill_vol - last_vol)
                
            result = (
                    f"Water Tank Volume\n"
                    f"Date: {date.today().strftime('%d-%m-%Y')} ({self.which_shift} Shift)\n\n"
            
                    f"6{self.first_time}: {first_vol}bbl ({first_dip}\")\n"
                    f"Before refill: {before_fill_vol}bbl\n"
                    f"After refill: {after_fill_vol}bbl\n"
                    f"6{self.last_time}: {last_vol}bbl ({last_dip}\")\n\n"
                    
                    f"Total consumption in 12hrs: {total_consum}bbl"
                )

        else:
            # No fill scenario
            total_consum = first_vol - last_vol
            result = (
                f"Water Tank Volume\n"
                f"Date: {date.today().strftime('%d-%m-%Y')} ({self.which_shift} Shift)\n\n"
                
                f"6{self.first_time}: {first_vol}bbl ({first_dip}\")\n"
                f"6{self.last_time}: {last_vol}bbl ({last_dip}\")\n\n"
                    
                f"Total consumption in 12hrs: {total_consum}bbl"
            )              
                
        self.show_result_dialog("Water Report", result)

kv_content = """
#:kivy 2.1.0

<MainMenuScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)
        
        MDIconButton:
            icon: 'theme-light-dark'
            pos_hint: {'x': 0, 'top': 1}
            on_release: root.toggle_theme()
        
        MDLabel:
            text: 'Water Tank Volume Calculator'
            halign: 'center'
            font_style: 'H3'
            
        MDRaisedButton:
            text: 'Convert to BBL'
            size_hint_x: 0.7
            pos_hint: {'center_x': .5}
            on_release: 
                root.manager.current = 'to_bbl'
                
        MDRaisedButton:
            text: 'Convert to Inches'
            size_hint_x: 0.7
            pos_hint: {'center_x': .5}
            on_release: 
                root.manager.current = 'to_inches'
                
        MDRaisedButton:
            text: 'Generate Report'
            size_hint_x: 0.7
            pos_hint: {'center_x': .5}
            on_release: 
                root.manager.current = 'generate_report'

<ToBBLScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(20)
        padding: dp(20)
        
        MDIconButton:
            icon: 'arrow-left'
            pos_hint: {'x': 0, 'top': 1}
            on_release: root.manager.current = 'main_menu'
        
        MDLabel:
            text: 'Inches to Barrels'
            halign: 'center'
            font_style: 'H4'
        
        MDTextField:
            id: dip_input
            hint_text: 'Enter Dip'
            helper_text: 'Inch'
            helper_text_mode: 'persistent'
            input_type: 'number'
            size_hint_x: 0.8
            pos_hint: {'center_x': .5}
        
        MDRaisedButton:
            text: 'Convert'
            pos_hint: {'center_x': .5}
            size_hint_x: 0.7
            on_release: root.calculate_volume()

<ToInchesScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(20)
        padding: dp(20)
        
        MDIconButton:
            icon: 'arrow-left'
            pos_hint: {'x': 0, 'top': 1}
            on_release: root.manager.current = 'main_menu'
        
        MDLabel:
            text: 'Barrels to Inches'
            halign: 'center'
            font_style: 'H4'
        
        MDTextField:
            id: barrel_input
            hint_text: 'Enter Volume'
            helper_text: 'bbl'
            helper_text_mode: 'persistent'
            input_type: 'number'
            size_hint_x: 0.8
            pos_hint: {'center_x': .5}
        
        MDRaisedButton:
            text: 'Convert'
            pos_hint: {'center_x': .5}
            size_hint_x: 0.7
            on_release: root.convert_to_inches()

<GenerateReportScreen>:
    ScrollView:
        MDBoxLayout:
            orientation: 'vertical'
            padding: dp(10)

            MDIconButton:
                icon: 'arrow-left'
                pos_hint: {'x': 0, 'top': 1}
                on_release: root.manager.current = 'main_menu'
                
            MDLabel:
                text: 'Water Report Generator'
                halign: 'center'
                font_style: 'H4'
                pos_hint: {'center_x': 0.5}

            MDBoxLayout:
                orientation: 'vertical'
                spacing: dp(20)
                padding: dp(20)

                MDBoxLayout:
                    orientation: 'horizontal'
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(40)

                    MDLabel:
                        text: "Shift (Day/Night)"
                        size_hint_x: 0.6

                    MDSwitch:
                        id: shift_switch
                        icon_active: "weather-night"
                        icon_inactive: "weather-sunny"
                        icon_inactive_color: "grey"
                        active: False
                        pos_hint: {'center_y': 0.5}
                        on_active: root.select_shift('night' if self.active else 'day')
                        
                MDBoxLayout:
                    orientation: 'horizontal'
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(40)

                    MDLabel:
                        text: "Refilled (No/Yes)"
                        size_hint_x: 0.6

                    MDSwitch:
                        id: filled_switch
                        icon_active: "check"
                        icon_inactive: "close"
                        icon_inactive_color: "grey"
                        active: False
                        pos_hint: {'center_y': 0.5}
                        on_active: root.toggle_filled(self.active)

            
                MDBoxLayout:
                    orientation: 'vertical'
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(350)
                    width: dp(300)
                        
                    MDTextField:
                        id: first_dip
                        hint_text: 'First Dip'
                        input_type: 'number'
                        helper_text: 'Inch'
                        helper_text_mode: 'persistent'

                    MDBoxLayout:
                        spacing: 30
                        id: fill_fields
                        height: dp(0)
                        opacity: 0
                        size_hint_y: None
                        pos_hint: {'center_x': .5}

                        MDTextField:
                            id: before_fill
                            hint_text: 'Before Refill Dip'
                            input_type: 'number'
                            disabled: 'True'
                            helper_text: 'Inch'
                            helper_text_mode: 'persistent'

                        MDTextField:
                            id: after_fill
                            hint_text: 'After Refill Dip'
                            input_type: 'number'
                            disabled: 'True'
                            helper_text: 'Inch'
                            helper_text_mode: 'persistent'

                    MDTextField:
                        id: last_dip
                        hint_text: 'Last Dip'
                        input_type: 'number'
                        helper_text: 'Inch'
                        helper_text_mode: 'persistent'

                MDRaisedButton:
                    text: 'Generate Report'
                    pos_hint: {'center_x': .5}
                    size_hint_x: 0.7
                    on_release: root.generate_report()

ScreenManager:
    MainMenuScreen:
        name: 'main_menu'
    ToBBLScreen:
        name: 'to_bbl'
    ToInchesScreen:
        name: 'to_inches'
    GenerateReportScreen:
        name: 'generate_report'
"""

kv_file_path = os.path.join(os.path.dirname(__file__), "waterCalc.kv")
with open(kv_file_path, "w") as kv_file:
    kv_file.write(kv_content)

class WaterCalc(MDApp):
    def build(self):
        Window.set_icon("assets/icon.png")
        self.theme_cls.primary_palette = "LightBlue"
        self.theme_cls.theme_style = "Dark"
        Window.softinput_mode = 'pan'
        Window.bind(on_keyboard=self.on_key_down)
        return Builder.load_file('waterCalc.kv')
    
    def on_key_down(self, window, key, *args):
        # Android back button
        if key == 27:  # ESC key is used as back button
            # Get current screen
            current_screen = self.root.current
            
            # Define navigation logic
            if current_screen == 'main_menu':
                # If on main menu, exit the app
                return False
            elif current_screen in ['to_bbl', 'to_inches', 'generate_report']:
                # Navigate back to main menu
                self.root.current = 'main_menu'
                return True
        
        # Let the event continue if not handled
        return False

if __name__ == '__main__':
    WaterCalc().run()
    

