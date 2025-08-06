import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


# Print configuration and standards
class PrintStandards:
	"""
	Centralized print formatting standards for consistent output
	"""

	# Standard paper sizes (width, height in points - 72 points per inch)
	PAPER_SIZES = {
		'letter': (612, 792),
		'legal': (612, 1008),
		'a4': (595, 842),
		'labels': (612, 792),  # Standard label sheet
	}

	# Standard margins (in points)
	MARGINS = {
		'normal': {'top': 72, 'bottom': 72, 'left': 72, 'right': 72},
		'narrow': {'top': 36, 'bottom': 36, 'left': 36, 'right': 36},
		'wide': {'top': 108, 'bottom': 108, 'left': 108, 'right': 108},
		'labels': {'top': 36, 'bottom': 36, 'left': 54, 'right': 54},
	}

	# Standard fonts and sizes
	FONTS = {
		'header': ('Helvetica-Bold', 16),
		'subheader': ('Helvetica-Bold', 14),
		'body': ('Helvetica', 11),
		'small': ('Helvetica', 9),
		'label': ('Helvetica', 10),
		'receipt': ('Courier', 10),
	}

	# Color schemes
	COLORS = {
		'black': (0, 0, 0),
		'dark_gray': (0.3, 0.3, 0.3),
		'gray': (0.5, 0.5, 0.5),
		'light_gray': (0.8, 0.8, 0.8),
		'white': (1, 1, 1),
		'accent': (1, 0.87, 0),  # #ffdf00 equivalent
	}

	# Standard layouts
	LAYOUTS = {
		'vendor_report': {
			'paper': 'letter',
			'margins': 'normal',
			'orientation': 'portrait'
		},
		'vendor_list': {
			'paper': 'letter',
			'margins': 'narrow',
			'orientation': 'landscape'
		},
		'mailing_labels': {
			'paper': 'labels',
			'margins': 'labels',
			'orientation': 'portrait'
		},
		'receipt': {
			'paper': 'letter',
			'margins': 'normal',
			'orientation': 'portrait'
		},
		'tax_stickers': {
			'paper': 'letter',
			'margins': 'narrow',
			'orientation': 'portrait'
		}
	}


class StandardizedDocument:
	"""Base class for standardized document generation"""

	def __init__(self, document_type: str, title: str = ""):
		self.document_type = document_type
		self.title = title or document_type.replace('_', ' ').title()
		self.layout = PrintStandards.LAYOUTS.get(document_type, PrintStandards.LAYOUTS['vendor_report'])
		self.content = []
		self.created_date = datetime.now()