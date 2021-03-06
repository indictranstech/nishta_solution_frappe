# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe.model.document import Document
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

class Domain(Document):
	'''Domain documents are created automatically when DocTypes
	with "Restricted" domains are imported during
	installation or migration'''
	def setup_domain(self):
		'''Setup domain icons, permissions, custom fields etc.'''
		self.setup_data()
		self.setup_roles()
		self.setup_properties()
		self.set_values()
		if not int(frappe.db.get_single_value('System Settings', 'setup_complete') or 0):
			# if setup not complete, setup desktop etc.
			self.setup_sidebar_items()
			self.setup_desktop_icons()
			self.set_default_portal_role()

		if self.data.custom_fields:
			create_custom_fields(self.data.custom_fields)

		if self.data.on_setup:
			# custom on_setup method
			frappe.get_attr(self.data.on_setup)()


	def setup_roles(self):
		'''Enable roles that are restricted to this domain'''
		if self.data.restricted_roles:
			for role_name in self.data.restricted_roles:
				role = frappe.get_doc('Role', role_name)
				role.disabled = 0
				role.save()

	def setup_data(self, domain=None):
		'''Load domain info via hooks'''
		self.data = frappe.get_domain_data(self.name)

	def get_domain_data(self, module):
		return frappe.get_attr(frappe.get_hooks('domains')[self.name] + '.data')

	def set_default_portal_role(self):
		'''Set default portal role based on domain'''
		if self.data.get('default_portal_role'):
			frappe.db.set_value('Portal Settings', None, 'default_role',
				self.data.get('default_portal_role'))

	def setup_desktop_icons(self):
		'''set desktop icons form `data.desktop_icons`'''
		from frappe.desk.doctype.desktop_icon.desktop_icon import set_desktop_icons
		if self.data.desktop_icons:
			set_desktop_icons(self.data.desktop_icons)

	def setup_properties(self):
		if self.data.properties:
			for args in self.data.properties:
				frappe.make_property_setter(args)


	def set_values(self):
		'''set values based on `data.set_value`'''
		if self.data.set_value:
			for args in self.data.set_value:
				doc = frappe.get_doc(args[0], args[1] or args[0])
				doc.set(args[2], args[3])
				doc.save()

	def setup_sidebar_items(self):
		'''Enable / disable sidebar items'''
		if self.data.allow_sidebar_items:
			# disable all
			frappe.db.sql('update `tabPortal Menu Item` set enabled=0')

			# enable
			frappe.db.sql('''update `tabPortal Menu Item` set enabled=1
				where route in ({0})'''.format(', '.join(['"{0}"'.format(d) for d in self.data.allow_sidebar_items])))

		if self.data.remove_sidebar_items:
			# disable all
			frappe.db.sql('update `tabPortal Menu Item` set enabled=1')

			# enable
			frappe.db.sql('''update `tabPortal Menu Item` set enabled=0
				where route in ({0})'''.format(', '.join(['"{0}"'.format(d) for d in self.data.remove_sidebar_items])))
