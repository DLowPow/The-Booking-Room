"""
Philosophy System - 4 Philosophies with unique origin stories
All promotions start with $0 and receive starting funds via inbox message
"""

from dataclasses import dataclass
from classes.enums import Philosophy


@dataclass
class PhilosophyProfile:
    name: str
    philosophy: Philosophy
    description: str
    # All start at $0 - grant comes from origin story
    starting_budget: int = 0
    starting_fans: int = 0
    prestige_start: int = 5
    merchandise_modifier: float = 1.0
    # Origin story
    starting_grant: int = 5000
    origin_sender: str = ""
    origin_subject: str = ""
    origin_message: str = ""
    # Gameplay modifiers
    match_rating_bonus: float = 0.0
    fan_growth_modifier: float = 1.0
    salary_modifier: float = 1.0


PHILOSOPHY_PROFILES = {
    Philosophy.STRONG_STYLE: PhilosophyProfile(
        name="Strong Style",
        philosophy=Philosophy.STRONG_STYLE,
        description="Hard-hitting, realistic combat. Stiff strikes and submission wrestling. Respect is earned in the ring.",
        starting_budget=0,
        starting_fans=0,
        prestige_start=5,
        merchandise_modifier=0.9,
        starting_grant=7000,
        origin_sender="Sensei Takahashi",
        origin_subject="Your Training is Complete",
        origin_message=(
            "Student,\n\n"
            "You have completed your training at my dojo. I have watched you grow from nothing "
            "into a warrior who understands the true spirit of professional wrestling.\n\n"
            "I am retiring and closing the dojo. I want you to carry on my legacy. "
            "Take this $7,000 — it is everything I have saved. Use it to build something real. "
            "Something that honours the art of Strong Style.\n\n"
            "Make me proud.\n\n"
            "— Sensei Takahashi"
        ),
        match_rating_bonus=0.15,
        fan_growth_modifier=0.9,
        salary_modifier=1.0,
    ),
    Philosophy.SPORTS_ENTERTAINMENT: PhilosophyProfile(
        name="Sports Entertainment",
        philosophy=Philosophy.SPORTS_ENTERTAINMENT,
        description="It's all about the show! Characters, storylines, and spectacle. Entertainment comes first.",
        starting_budget=0,
        starting_fans=0,
        prestige_start=3,
        merchandise_modifier=1.3,
        starting_grant=10000,
        origin_sender="Solicitors - Henderson & Wright",
        origin_subject="RE: Estate of Gerald 'The Showman' Wright",
        origin_message=(
            "Dear Sir/Madam,\n\n"
            "We are writing to inform you that your Great Uncle, Gerald 'The Showman' Wright, "
            "has sadly passed away.\n\n"
            "Mr. Wright was a travelling showman and entertainer for over 40 years. "
            "In his will, he has left you the sum of $10,000, along with a note that reads:\n\n"
            "\"The world needs more entertainment. Put on a show, kid.\"\n\n"
            "The funds have been transferred to your account.\n\n"
            "Our condolences,\n"
            "Henderson & Wright Solicitors"
        ),
        match_rating_bonus=-0.1,
        fan_growth_modifier=1.3,
        salary_modifier=1.1,
    ),
    Philosophy.LUCHA_LIBRE: PhilosophyProfile(
        name="Lucha Libre",
        philosophy=Philosophy.LUCHA_LIBRE,
        description="High-flying, colourful, and acrobatic. Masks, tradition, and honour. The art of Lucha.",
        starting_budget=0,
        starting_fans=0,
        prestige_start=5,
        merchandise_modifier=1.1,
        starting_grant=6000,
        origin_sender="Abuela Rosa",
        origin_subject="Your Grandfather's Mask",
        origin_message=(
            "Mi nieto,\n\n"
            "I found this box in the attic. Inside was your grandfather's mask — "
            "the mask of El Águila Dorada. He wrestled in the plazas of Mexico City for 30 years.\n\n"
            "He always said you had the fire in your blood. I have sold some of his old ring gear "
            "and memorabilia. Here is $6,000. It is not much, but it is enough to start.\n\n"
            "Carry the mask. Carry the tradition. Make your grandfather proud.\n\n"
            "Con amor,\n"
            "Abuela Rosa"
        ),
        match_rating_bonus=0.05,
        fan_growth_modifier=1.1,
        salary_modifier=0.9,
    ),
    Philosophy.ULTRAVIOLENT: PhilosophyProfile(
        name="Ultraviolent",
        philosophy=Philosophy.ULTRAVIOLENT,
        description="Extreme violence taken to the limit. Weapons, blood, and brutality. Not for the faint-hearted.",
        starting_budget=0,
        starting_fans=0,
        prestige_start=1,
        merchandise_modifier=0.7,
        starting_grant=3500,
        origin_sender="Department for Work and Pensions",
        origin_subject="RE: Your Disability Assessment Results",
        origin_message=(
            "Dear Applicant,\n\n"
            "Following your recent assessment, we can confirm that you have been found "
            "unfit for standard employment due to your existing conditions.\n\n"
            "You are entitled to a monthly Personal Independence Payment. "
            "Additionally, a one-off Enterprise Allowance of $3,500 has been approved "
            "to support you in establishing a self-employed venture.\n\n"
            "Please use these funds responsibly.\n\n"
            "Regards,\n"
            "Department for Work and Pensions\n"
            "Benefits Assessment Team"
        ),
        match_rating_bonus=-0.1,
        fan_growth_modifier=0.7,
        salary_modifier=0.7,
    ),
}


def get_philosophy_profile(philosophy: Philosophy) -> PhilosophyProfile:
    return PHILOSOPHY_PROFILES.get(philosophy, PHILOSOPHY_PROFILES[Philosophy.STRONG_STYLE])
