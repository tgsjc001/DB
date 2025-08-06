from models import Session
from models.activity_log import ActivityLog
from models.audit_log import AuditLog
from datetime import datetime
import json
import traceback
from functools import wraps


class EnhancedLogger:
	"""
	Enhanced logging system with detailed context tracking
	"""

	def __init__(self, user):
		self.user = user
		self.session_context = {
			"session_id": datetime.now().isoformat(),
			"user_id": user.id,
			"username": user.username,
			"role": user.role
		}

	def log_vendor_interaction(self, action, vendor_id=None, vendor_data=None,
							   changes=None, context=None):
		"""Log detailed vendor interactions"""
		try:
			description_parts = []

			if vendor_data:
				vendor_name = (vendor_data.get('business_name') or
							   f"{vendor_data.get('first_name', '')} {vendor_data.get('last_name', '')}").strip()
				description_parts.append(f"Vendor: {vendor_name}")

			if vendor_id:
				description_parts.append(f"ID: {vendor_id}")

			if changes:
				description_parts.append(f"Changes: {json.dumps(changes, default=str)}")

			if context:
				description_parts.append(f"Context: {context}")

			description = " | ".join(description_parts)

			self._log_activity(f"Vendor {action}", description)

			# Also log to audit for important actions
			if action in ["Created", "Updated", "Deleted", "Exported", "Printed"]:
				self._log_audit(f"Vendor {action}", description)

		except Exception as e:
			print(f"[ERROR] Vendor logging failed: {e}")

	def log_form_interaction(self, form_type, action, form_data=None,
							 field_changes=None, duration=None):
		"""Log form interactions with detailed field tracking"""
		try:
			description_parts = [f"Form: {form_type}", f"Action: {action}"]

			if duration:
				description_parts.append(f"Duration: {duration:.1f}s")

			if field_changes:
				# Track specific field changes
				changes_summary = {}
				for field, (old_val, new_val) in field_changes.items():
					if old_val != new_val:
						changes_summary[field] = {
							"from": str(old_val)[:50] + "..." if len(str(old_val)) > 50 else str(old_val),
							"to": str(new_val)[:50] + "..." if len(str(new_val)) > 50 else str(new_val)
						}

				if changes_summary:
					description_parts.append(f"Changed fields: {json.dumps(changes_summary)}")

			if form_data and action in ["Saved", "Created"]:
				# Log key identifiers
				if form_type == "Vendor":
					name = (form_data.get('business_name') or
							f"{form_data.get('first_name', '')} {form_data.get('last_name', '')}").strip()
					if name:
						description_parts.append(f"Record: {name}")
				elif form_type == "Mailout":
					name = form_data.get('name', '')
					if name:
						description_parts.append(f"Record: {name}")

			description = " | ".join(description_parts)
			self._log_activity(f"Form {action}", description)

		except Exception as e:
			print(f"[ERROR] Form logging failed: {e}")

	def log_search_filter(self, search_term=None, filters=None, results_count=None, module="Unknown"):
		"""Log search and filter usage"""
		try:
			description_parts = [f"Module: {module}"]

			if search_term:
				description_parts.append(f"Search: '{search_term}'")

			if filters:
				active_filters = [k for k, v in filters.items() if v and hasattr(v, 'get') and v.get()]
				if active_filters:
					description_parts.append(f"Filters: {', '.join(active_filters)}")

			if results_count is not None:
				description_parts.append(f"Results: {results_count}")

			description = " | ".join(description_parts)
			self._log_activity("Search/Filter", description)

		except Exception as e:
			print(f"[ERROR] Search logging failed: {e}")

	def log_export_print(self, action, export_type, record_count=None,
						 file_path=None, filters_applied=None):
		"""Log export and print operations"""
		try:
			description_parts = [f"Type: {export_type}"]

			if record_count is not None:
				description_parts.append(f"Records: {record_count}")

			if file_path:
				description_parts.append(f"File: {file_path}")

			if filters_applied:
				description_parts.append(f"Filters: {filters_applied}")

			description = " | ".join(description_parts)

			self._log_activity(f"{action} {export_type}", description)
			self._log_audit(f"{action} Operation", description)

		except Exception as e:
			print(f"[ERROR] Export logging failed: {e}")

	def log_navigation(self, from_module, to_module, method="Unknown"):
		"""Log user navigation patterns"""
		try:
			description = f"From: {from_module} | To: {to_module} | Method: {method}"
			self._log_activity("Navigation", description)
		except Exception as e:
			print(f"[ERROR] Navigation logging failed: {e}")

	def log_error(self, error_type, error_message, context=None, stack_trace=None):
		"""Log system errors with context"""
		try:
			description_parts = [f"Error: {error_type}", f"Message: {error_message}"]

			if context:
				description_parts.append(f"Context: {context}")

			if stack_trace:
				# Limit stack trace length for database storage
				short_trace = stack_trace[:500] + "..." if len(stack_trace) > 500 else stack_trace
				description_parts.append(f"Stack: {short_trace}")

			description = " | ".join(description_parts)

			self._log_activity("System Error", description)
			self._log_audit("System Error", description)

		except Exception as e:
			print(f"[ERROR] Error logging failed: {e}")

	def log_double_click(self, item_type, item_id, item_data=None, context=None):
		"""Log double-click interactions with detailed context"""
		try:
			description_parts = [f"Item: {item_type}", f"ID: {item_id}"]

			if item_data:
				if item_type == "Vendor":
					name = (item_data.get('business_name') or
							f"{item_data.get('first_name', '')} {item_data.get('last_name', '')}").strip()
					location = f"{item_data.get('island', '')} {item_data.get('row', '')} {item_data.get('table_numbers', '')}".strip()
					description_parts.extend([f"Name: {name}", f"Location: {location}"])

				elif item_type == "Mailout":
					name = item_data.get('name', '')
					city = f"{item_data.get('city', '')}, {item_data.get('state', '')}"
					description_parts.extend([f"Name: {name}", f"Location: {city}"])

			if context:
				description_parts.append(f"Context: {context}")

			description = " | ".join(description_parts)
			self._log_activity(f"Double-Click {item_type}", description)

		except Exception as e:
			print(f"[ERROR] Double-click logging failed: {e}")

	def log_bulk_operation(self, operation, affected_count, criteria=None, results=None):
		"""Log bulk operations like mass updates or deletions"""
		try:
			description_parts = [f"Operation: {operation}", f"Count: {affected_count}"]

			if criteria:
				description_parts.append(f"Criteria: {criteria}")

			if results:
				description_parts.append(f"Results: {results}")

			description = " | ".join(description_parts)

			self._log_activity(f"Bulk {operation}", description)
			self._log_audit(f"Bulk {operation}", description)

		except Exception as e:
			print(f"[ERROR] Bulk operation logging failed: {e}")

	def _log_activity(self, action, description):
		"""Internal method to log to activity log"""
		try:
			session = Session()
			log = ActivityLog(
				user_id=self.user.id,
				username=self.user.username,
				action=action,
				description=description,
				timestamp=datetime.utcnow(),
				visible=True
			)
			session.add(log)
			session.commit()
			session.close()
		except Exception as e:
			print(f"[ERROR] Activity logging to database failed: {e}")

	def _log_audit(self, action, description):
		"""Internal method to log to audit log"""
		try:
			session = Session()
			log = AuditLog(
				user_id=self.user.id,
				username=self.user.username,
				action=action,
				description=description,
				timestamp=datetime.utcnow(),
				visible=True
			)
			session.add(log)
			session.commit()
			session.close()
		except Exception as e:
			print(f"[ERROR] Audit logging to database failed: {e}")


# Decorator for automatic logging of function calls
def log_function_call(logger, action_name=None):
	"""Decorator to automatically log function calls"""

	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			action = action_name or f"{func.__name__}"
			start_time = datetime.now()

			try:
				result = func(*args, **kwargs)
				duration = (datetime.now() - start_time).total_seconds()

				logger.log_form_interaction(
					form_type="System",
					action=f"{action} Completed",
					duration=duration
				)
				return result

			except Exception as e:
				duration = (datetime.now() - start_time).total_seconds()
				logger.log_error(
					error_type=type(e).__name__,
					error_message=str(e),
					context=f"Function: {action}",
					stack_trace=traceback.format_exc()
				)
				raise

		return wrapper

	return decorator


# Context manager for tracking form sessions
class FormSession:
	"""Context manager to track form editing sessions"""

	def __init__(self, logger, form_type, form_id=None):
		self.logger = logger
		self.form_type = form_type
		self.form_id = form_id
		self.start_time = None
		self.original_data = {}
		self.field_changes = {}

	def __enter__(self):
		self.start_time = datetime.now()
		self.logger.log_form_interaction(
			form_type=self.form_type,
			action="Opened",
			form_data={"id": self.form_id} if self.form_id else None
		)
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		duration = (datetime.now() - self.start_time).total_seconds()

		if exc_type:
			self.logger.log_error(
				error_type=exc_type.__name__,
				error_message=str(exc_val),
				context=f"Form: {self.form_type}",
				stack_trace=traceback.format_exc()
			)
			action = "Error"
		else:
			action = "Closed"

		self.logger.log_form_interaction(
			form_type=self.form_type,
			action=action,
			field_changes=self.field_changes,
			duration=duration
		)

	def track_field_change(self, field_name, old_value, new_value):
		"""Track individual field changes"""
		self.field_changes[field_name] = (old_value, new_value)

	def set_original_data(self, data):
		"""Set the original form data for comparison"""
		self.original_data = data.copy() if data else {}


# Utility function to create logger instance
def get_enhanced_logger(user):
	"""Factory function to create enhanced logger instance"""
	return EnhancedLogger(user)