"""Pre-built list templates for common operations."""

# Standard list templates for bitcoin mining operations

LIST_TEMPLATES = {
    "daily_generator_inspection": {
        "name": "Daily Generator Inspection",
        "category": "inspection",
        "list_type": "checklist",
        "items": [
            {
                "title": "Check oil level",
                "description": "Ensure oil is between min and max marks",
                "estimated_duration_minutes": 5,
                "expected_values": ["OK", "Low", "Critical"],
            },
            {
                "title": "Check coolant level",
                "description": "Verify coolant is at proper level",
                "estimated_duration_minutes": 3,
                "expected_values": ["OK", "Low", "Empty"],
            },
            {
                "title": "Inspect belts",
                "description": "Check for wear, cracks, or loose tension",
                "estimated_duration_minutes": 5,
                "expected_values": ["Good", "Worn", "Replace"],
            },
            {
                "title": "Check air filters",
                "description": "Inspect and clean if necessary",
                "estimated_duration_minutes": 10,
                "expected_values": ["Clean", "Dirty", "Replace"],
            },
            {
                "title": "Check fuel level",
                "description": "Record current fuel percentage",
                "estimated_duration_minutes": 2,
                "requires_note": True,
            },
            {
                "title": "Test emergency shutdown",
                "description": "Verify E-stop functions correctly",
                "estimated_duration_minutes": 5,
                "expected_values": ["Pass", "Fail"],
            },
            {
                "title": "Record hour meter reading",
                "description": "Log current hours for maintenance tracking",
                "estimated_duration_minutes": 2,
                "requires_note": True,
            },
            {
                "title": "Check for leaks",
                "description": "Inspect for oil, coolant, or fuel leaks",
                "estimated_duration_minutes": 5,
                "expected_values": ["None", "Minor", "Major"],
                "requires_photo": True,
            },
        ],
    },
    "weekly_maintenance": {
        "name": "Weekly Maintenance Checklist",
        "category": "maintenance",
        "list_type": "sequential",
        "items": [
            {
                "title": "Shut down equipment safely",
                "description": "Follow proper shutdown procedure",
                "estimated_duration_minutes": 10,
                "priority": "high",
            },
            {
                "title": "Change oil",
                "description": "Drain old oil and replace with new",
                "estimated_duration_minutes": 30,
                "priority": "high",
            },
            {
                "title": "Replace oil filter",
                "description": "Install new oil filter",
                "estimated_duration_minutes": 10,
            },
            {
                "title": "Clean or replace air filters",
                "description": "Based on inspection results",
                "estimated_duration_minutes": 15,
            },
            {
                "title": "Check battery connections",
                "description": "Clean terminals if corroded",
                "estimated_duration_minutes": 10,
            },
            {
                "title": "Grease fittings",
                "description": "Apply grease to all zerk fittings",
                "estimated_duration_minutes": 15,
            },
            {
                "title": "Test run equipment",
                "description": "Verify proper operation after maintenance",
                "estimated_duration_minutes": 15,
                "priority": "high",
            },
            {
                "title": "Update maintenance log",
                "description": "Record all work performed",
                "estimated_duration_minutes": 5,
                "requires_note": True,
            },
        ],
    },
    "site_startup": {
        "name": "Site Startup Procedure",
        "category": "startup",
        "list_type": "sequential",
        "items": [
            {
                "title": "Safety walk-around",
                "description": "Check for hazards or obstacles",
                "estimated_duration_minutes": 10,
                "priority": "high",
            },
            {
                "title": "Check main power disconnect",
                "description": "Ensure in OFF position",
                "estimated_duration_minutes": 2,
            },
            {
                "title": "Verify ventilation is clear",
                "description": "No blockages in air intake/exhaust",
                "estimated_duration_minutes": 5,
            },
            {
                "title": "Check generator fluids",
                "description": "Oil, coolant, fuel levels",
                "estimated_duration_minutes": 10,
            },
            {
                "title": "Start generator",
                "description": "Follow manufacturer startup procedure",
                "estimated_duration_minutes": 5,
            },
            {
                "title": "Monitor for abnormal conditions",
                "description": "Listen for unusual sounds, check gauges",
                "estimated_duration_minutes": 10,
                "requires_note": True,
            },
            {
                "title": "Enable main power",
                "description": "Turn on main disconnect",
                "estimated_duration_minutes": 2,
            },
            {
                "title": "Verify miner connectivity",
                "description": "Check that miners are coming online",
                "estimated_duration_minutes": 15,
            },
            {
                "title": "Check telemetry data",
                "description": "Confirm remote monitoring is active",
                "estimated_duration_minutes": 5,
            },
            {
                "title": "Log startup completion",
                "description": "Record time and any issues",
                "estimated_duration_minutes": 5,
                "requires_note": True,
            },
        ],
    },
    "emergency_shutdown": {
        "name": "Emergency Shutdown Procedure",
        "category": "shutdown",
        "list_type": "sequential",
        "priority": "urgent",
        "items": [
            {
                "title": "Hit emergency stop",
                "description": "Press E-stop button immediately",
                "estimated_duration_minutes": 1,
                "priority": "urgent",
            },
            {
                "title": "Turn off main disconnect",
                "description": "Shut off main power",
                "estimated_duration_minutes": 1,
                "priority": "urgent",
            },
            {
                "title": "Check for injuries",
                "description": "Ensure all personnel are safe",
                "estimated_duration_minutes": 5,
                "priority": "urgent",
            },
            {
                "title": "Document incident",
                "description": "Record what triggered shutdown",
                "estimated_duration_minutes": 10,
                "requires_note": True,
                "requires_photo": True,
            },
            {
                "title": "Notify management",
                "description": "Call supervisor immediately",
                "estimated_duration_minutes": 5,
                "priority": "high",
            },
            {
                "title": "Secure the site",
                "description": "Ensure area is safe before leaving",
                "estimated_duration_minutes": 10,
            },
        ],
    },
    "monthly_deep_inspection": {
        "name": "Monthly Deep Inspection",
        "category": "inspection",
        "list_type": "checklist",
        "items": [
            {
                "title": "Inspect electrical connections",
                "description": "Check for loose connections, burns, corrosion",
                "estimated_duration_minutes": 30,
                "priority": "high",
                "requires_photo": True,
            },
            {
                "title": "Test transfer switch",
                "description": "Verify automatic transfer switch operation",
                "estimated_duration_minutes": 20,
            },
            {
                "title": "Clean radiator fins",
                "description": "Remove debris and clean thoroughly",
                "estimated_duration_minutes": 45,
            },
            {
                "title": "Check exhaust system",
                "description": "Inspect for leaks, damage, or blockages",
                "estimated_duration_minutes": 20,
            },
            {
                "title": "Test all safety systems",
                "description": "Overspeed, high temp, low oil pressure",
                "estimated_duration_minutes": 30,
                "priority": "high",
            },
            {
                "title": "Inspect fuel system",
                "description": "Check lines, filters, and tank condition",
                "estimated_duration_minutes": 25,
            },
            {
                "title": "Vibration analysis",
                "description": "Check for unusual vibrations or noises",
                "estimated_duration_minutes": 15,
                "requires_note": True,
            },
            {
                "title": "Update equipment records",
                "description": "Log all findings and maintenance performed",
                "estimated_duration_minutes": 20,
                "requires_note": True,
            },
        ],
    },
    "contractor_site_visit": {
        "name": "Contractor Site Visit Checklist",
        "category": "general",
        "list_type": "checklist",
        "items": [
            {
                "title": "Verify contractor credentials",
                "description": "Check ID and work authorization",
                "estimated_duration_minutes": 5,
            },
            {
                "title": "Safety briefing",
                "description": "Review site hazards and emergency procedures",
                "estimated_duration_minutes": 10,
                "priority": "high",
            },
            {
                "title": "Define work scope",
                "description": "Confirm what work will be performed",
                "estimated_duration_minutes": 15,
                "requires_note": True,
            },
            {
                "title": "Show equipment locations",
                "description": "Point out relevant equipment and shutoffs",
                "estimated_duration_minutes": 10,
            },
            {
                "title": "Review hot work permit",
                "description": "If welding/cutting required",
                "estimated_duration_minutes": 10,
                "is_optional": True,
            },
            {
                "title": "Monitor work progress",
                "description": "Periodic checks during work",
                "estimated_duration_minutes": 30,
            },
            {
                "title": "Inspect completed work",
                "description": "Verify work meets requirements",
                "estimated_duration_minutes": 20,
                "requires_photo": True,
            },
            {
                "title": "Sign off on completion",
                "description": "Document work completed and any issues",
                "estimated_duration_minutes": 10,
                "requires_note": True,
            },
        ],
    },
}


def get_template(template_key: str) -> dict:
    """Get a specific template by key."""
    return LIST_TEMPLATES.get(template_key)


def get_all_templates() -> dict:
    """Get all available templates."""
    return LIST_TEMPLATES


def get_templates_by_category(category: str) -> dict:
    """Get templates filtered by category."""
    return {
        key: template
        for key, template in LIST_TEMPLATES.items()
        if template.get("category") == category
    }
