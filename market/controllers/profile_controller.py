import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from market.views.main_view import Ui_MainWindow
from marketGUI.market_app import MarketApplication
from market.api.api import MarketAPI


class ProfileController:
    def __init__(self, mainwindow):
        # self.mainwindow = Ui_MainWindow  # Comment before running
        self.mainwindow = mainwindow  # Uncomment before running
        self.current_profile = None
        self.payload = {}
        # check if the profile already exists
        # self.user = self.mainwindow.app.user
        self.mainwindow.profile_save_pushbutton.clicked.connect(self.save_form)


    def setup_view(self):
        self.current_profile = self.mainwindow.api.load_profile(self.mainwindow.app.user)
        # print 'Profile: Current profile: ',
        # print self.current_profile
        if self.current_profile:
            self.mainwindow.profile_firstname_lineedit.setText(self.current_profile['first_name'])
            self.mainwindow.profile_lastname_lineedit.setText(self.current_profile['last_name'])
            self.mainwindow.profile_email_lineedit.setText(self.current_profile['email'])
            self.mainwindow.profile_iban_lineedit.setText(self.current_profile['iban'])
            self.mainwindow.profile_phonenumber_lineedit.setText(self.current_profile['phonenumber'])

            if self.current_profile['role'] == 1:
                self.mainwindow.profile_borrower_radiobutton.setChecked(True)
                self.payload['role'] = 1
                self.mainwindow.profile_postcode_lineedit.setText(self.current_profile['current_postalcode'])
                self.mainwindow.profile_housenumber_lineedit.setText(self.current_profile['current_housenumber'])
                # missing 'documents_list': self.documentsTable
            else:
                self.mainwindow.profile_investor_radiobutton.setChecked(True)
        else:
            print 'Profile: Current profile is empty'



    def show_current_profile(self):
        # if self.current_profile:
        pass

    def save_form(self):
        self.payload = {'role': 2, 'first_name': str(self.mainwindow.profile_firstname_lineedit.text()),
                        'last_name': str(self.mainwindow.profile_lastname_lineedit.text()),
                        'email': str(self.mainwindow.profile_email_lineedit.text()),
                        'iban': str(self.mainwindow.profile_iban_lineedit.text()),
                        'phonenumber': str(self.mainwindow.profile_phonenumber_lineedit.text())}

        # for key in self._basic_forms:
        #     payload[key] = self._basic_forms[key].text()

        if self.mainwindow.profile_borrower_radiobutton.isChecked():
            self.payload['role'] = 1
            self.payload['current_postalcode'] = str(self.mainwindow.profile_postcode_lineedit.text())
            self.payload['current_housenumber'] = str(self.mainwindow.profile_housenumber_lineedit.text()) # missing 'documents_list': self.documentsTable
            self.payload['documents_list'] = []
        # print self.payload
        print 'creating profile:'
        print self.mainwindow.api.create_profile(self.mainwindow.app.user, self.payload)
        # TODO prompt: profile is created
        if self.mainwindow.api.create_profile(self.mainwindow.app.user, self.payload):
            QMessageBox.about(self.mainwindow, "My message box", 'Profile saved.')
            # print 'check if the profile has been added:'
            # print self.mainwindow.api.load_profile(self.mainwindow.app.user)
