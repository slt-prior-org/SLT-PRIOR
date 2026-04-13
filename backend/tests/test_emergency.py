"""
Yksikkötestit hätätilannetunnistukselle (emergency.py).
"""

import pytest
import sys
import os

# Lisää src-hakemisto importteihin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai_model.emergency import detect_emergency, EmergencyResult

pytestmark = pytest.mark.unit

# ---------- Englanninkieliset hätäsanat ----------

class TestEnglishKeywords:
    def test_heart_attack(self):
        result = detect_emergency("I think I'm having a heart attack")
        assert result is not None
        assert any("heart attack" in kw for kw in result.matched_keywords)

    def test_stroke(self):
        result = detect_emergency("I think my dad is having a stroke")
        assert result is not None

    def test_cant_breathe(self):
        result = detect_emergency("I can't breathe properly")
        assert result is not None

    def test_cannot_breathe(self):
        result = detect_emergency("My mother cannot breathe")
        assert result is not None

    def test_unconscious(self):
        result = detect_emergency("He is unconscious on the floor")
        assert result is not None

    def test_cardiac_arrest(self):
        result = detect_emergency("Someone is in cardiac arrest")
        assert result is not None

    def test_call_ambulance(self):
        result = detect_emergency("Should I call an ambulance?")
        assert result is not None

    def test_im_dying(self):
        result = detect_emergency("I think I'm dying")
        assert result is not None

    def test_cpr(self):
        result = detect_emergency("How do I perform CPR right now?")
        assert result is not None

    def test_choking(self):
        result = detect_emergency("My child is choking")
        assert result is not None

    def test_severe_bleeding(self):
        result = detect_emergency("There is severe bleeding from the wound")
        assert result is not None


# ---------- Suomenkieliset hätäsanat ----------

class TestFinnishKeywords:
    def test_sydankohtaus(self):
        result = detect_emergency("Minulla on sydänkohtaus")
        assert result is not None

    #def test_rintakipu(self):
    #    result = detect_emergency("Minulla on kova rintakipu")
    #    assert result is not None

    def test_aivohalvaus(self):
        result = detect_emergency("Isälläni on aivohalvaus")
        assert result is not None

    def test_hengitysvaikeus(self):
        result = detect_emergency("Minulla on hengitysvaikeuksia")
        assert result is not None

    def test_en_pysty_hengittamaan(self):
        result = detect_emergency("En pysty hengittämään")
        assert result is not None

    def test_tajuton(self):
        result = detect_emergency("Hän on tajuton")
        assert result is not None

    def test_elvytys(self):
        result = detect_emergency("Tarvitsen elvytysohjeita nyt")
        assert result is not None

    def test_soita_112(self):
        result = detect_emergency("Pitääkö soita 112?")
        assert result is not None

    def test_ambulanssi(self):
        result = detect_emergency("Tarvitsen ambulanssin")
        assert result is not None

    def test_hengenahdistus(self):
        result = detect_emergency("Minulla on hengenahdistus")
        assert result is not None

    def test_kuolen(self):
        result = detect_emergency("Minä kuolen")
        assert result is not None

    def test_en_saa_henkea(self):
        result = detect_emergency("En saa henkeä")
        assert result is not None


# ---------- Suomen taivutusmuodot (regex) ----------

class TestFinnishMorphology:
    #def test_rintakipua(self):
    #    result = detect_emergency("Minulla on rintakipua")
    #    assert result is not None

    #def test_rintakipuja(self):
    #    result = detect_emergency("Onko rintakipuja normaalia?")
    #    assert result is not None

    def test_sydankohtauksen(self):
        result = detect_emergency("Sydänkohtauksen oireet")
        assert result is not None

    def test_sydankohtausta(self):
        result = detect_emergency("Minulla on sydänkohtausta")
        assert result is not None

    def test_aivohalvauksen(self):
        result = detect_emergency("Aivohalvauksen oireet")
        assert result is not None

    def test_tajuttomana(self):
        result = detect_emergency("Hän makaa tajuttomana")
        assert result is not None

    def test_tajuttomuuden(self):
        result = detect_emergency("Tajuttomuuden syyt")
        assert result is not None

    def test_elvytysta(self):
        result = detect_emergency("Aloita elvytystä")
        assert result is not None

    def test_hengenahdistusta(self):
        result = detect_emergency("Kärsin hengenahdistusta")
        assert result is not None

    def test_hengitysvaikeuksista(self):
        result = detect_emergency("Kärsin hengitysvaikeuksista")
        assert result is not None

    def test_elvyttaa(self):
        result = detect_emergency("Pitääkö elvyttää?")
        assert result is not None

    def test_elvyttakaa(self):
        result = detect_emergency("Elvyttäkää häntä!")
        assert result is not None

    def test_elvytan(self):
        result = detect_emergency("Elvytän häntä nyt")
        assert result is not None

    def test_elvytetaan(self):
        result = detect_emergency("Elvytetään heti")
        assert result is not None

    def test_elvyttamaan(self):
        result = detect_emergency("Aletaan elvyttämään")
        assert result is not None

    def test_kouristaa(self):
        result = detect_emergency("Häntä kouristaa")
        assert result is not None

    def test_kouristuksia(self):
        result = detect_emergency("Hänellä on kouristuksia")
        assert result is not None

    def test_kuolee(self):
        result = detect_emergency("Hän kuolee")
        assert result is not None

    def test_kuollut(self):
        result = detect_emergency("Hän on kuollut")
        assert result is not None

    def test_pyortyi(self):
        result = detect_emergency("Hän pyörtyi")
        assert result is not None

    def test_pyortynyt(self):
        result = detect_emergency("Hän on pyörtynyt")
        assert result is not None

    def test_tukehtui(self):
        result = detect_emergency("Lapsi tukehtui")
        assert result is not None

    def test_tukehtumassa(self):
        result = detect_emergency("Hän on tukehtumassa")
        assert result is not None

    def test_aivoverenvuodon(self):
        result = detect_emergency("Aivoverenvuodon oireet")
        assert result is not None

    def test_ambulanssin(self):
        result = detect_emergency("Tilaa ambulanssin")
        assert result is not None


# ---------- Ei-hätätilanteet ----------

class TestNonEmergencies:
    def test_general_question(self):
        result = detect_emergency("Mikä on sepelvaltimotauti?")
        assert result is None

    def test_diet_question(self):
        result = detect_emergency("Millainen ruokavalio on hyväksi sydämelle?")
        assert result is None

    def test_exercise_question(self):
        result = detect_emergency("Kuinka paljon pitäisi liikkua päivässä?")
        assert result is None

    def test_medication_question(self):
        result = detect_emergency("What does aspirin do?")
        assert result is None

    def test_blood_pressure_general(self):
        result = detect_emergency("What is normal blood pressure?")
        assert result is None

    def test_greeting(self):
        result = detect_emergency("Hei, miten voit?")
        assert result is None

    def test_risk_factors(self):
        result = detect_emergency("What are the risk factors for heart disease?")
        assert result is None

    def test_cholesterol(self):
        result = detect_emergency("Mikä on kolesteroli?")
        assert result is None


# ---------- Tyhjät ja erikoisviestit ----------

class TestEdgeCases:
    def test_empty_string(self):
        result = detect_emergency("")
        assert result is None

    def test_none_message(self):
        result = detect_emergency(None)
        assert result is None

    def test_whitespace_only(self):
        result = detect_emergency("   ")
        assert result is None

    def test_single_character(self):
        result = detect_emergency("a")
        assert result is None


# ---------- Case-insensitivity ----------

class TestCaseInsensitivity:
    def test_uppercase_english(self):
        result = detect_emergency("I AM HAVING A HEART ATTACK")
        assert result is not None

    def test_mixed_case_english(self):
        result = detect_emergency("I Am Having A Heart Attack")
        assert result is not None

    def test_uppercase_finnish(self):
        result = detect_emergency("SYDÄNKOHTAUS")
        assert result is not None

    #def test_mixed_case_finnish(self):
    #    result = detect_emergency("Rintakipu on kova")
    #    assert result is not None


# ---------- Vastauksen rakenne ----------

class TestResponseStructure:
    def test_result_has_correct_type(self):
        result = detect_emergency("heart attack")
        assert isinstance(result, EmergencyResult)

    def test_result_has_matched_keywords(self):
        result = detect_emergency("heart attack")
        assert len(result.matched_keywords) > 0

    def test_result_has_finnish_message(self):
        result = detect_emergency("heart attack")
        assert "112" in result.emergency_message_fi
        assert len(result.emergency_message_fi) > 0

    def test_result_has_combined_message(self):
        result = detect_emergency("heart attack")
        assert "112" in result.emergency_message_en
        assert len(result.emergency_message_en) > 0

    def test_combined_message_contains_both_languages(self):
        result = detect_emergency("heart attack")
        # emergency_message_en contains both FI and EN (combined)
        assert "hätänumeroon" in result.emergency_message_en
        assert "emergency number" in result.emergency_message_en


# ---------- False positive -vähennys ----------

class TestFalsePositiveReduction:
    # Kasvatukselliset kysymykset (FI) → None
    def test_fi_edu_elvytetaan(self):
        result = detect_emergency("Kuinka elvytetään?")
        assert result is None

    def test_fi_edu_aivohalvaus_yleisesti(self):
        result = detect_emergency("Aivohalvauksen oireet yleisesti?")
        assert result is None

    def test_fi_edu_sydankohtaus_tunnistetaan(self):
        result = detect_emergency("Miten sydänkohtaus tunnistetaan?")
        assert result is None

    def test_fi_edu_kerro_elvytyksesta(self):
        result = detect_emergency("Kerro elvytyksestä")
        assert result is None

    # Kielikuvat (FI) → None
    def test_fi_fig_kuolen_nalkaan(self):
        result = detect_emergency("Kuolen nälkään")
        assert result is None

    def test_fi_fig_kuolen_nauruun(self):
        result = detect_emergency("Kuolen nauruun")
        assert result is None

    # Menneisyys (FI) → None
    def test_fi_past_sai_sydankohtauksen(self):
        result = detect_emergency("Isäni sai sydänkohtauksen viime vuonna")
        assert result is None

    def test_fi_past_koki_aivohalvauksen(self):
        result = detect_emergency("Äitini koki aivohalvauksen kauan sitten")
        assert result is None

    # Kasvatukselliset kysymykset (EN) → None
    def test_en_edu_what_is_heart_attack(self):
        result = detect_emergency("What is a heart attack?")
        assert result is None

    def test_en_edu_how_do_stroke_symptoms(self):
        result = detect_emergency("How do stroke symptoms appear?")
        assert result is None

    def test_en_edu_tell_me_about_cardiac_arrest(self):
        result = detect_emergency("Tell me about cardiac arrest")
        assert result is None

    # Kielikuvat (EN) → None
    def test_en_fig_dying_of_laughter(self):
        result = detect_emergency("I am dying of laughter")
        assert result is None

    def test_en_fig_dying_of_boredom(self):
        result = detect_emergency("I'm dying of boredom")
        assert result is None

    # Menneisyys (EN) → None
    def test_en_past_grandfather_heart_attack(self):
        result = detect_emergency("My grandfather had a heart attack in 1998")
        assert result is None

    def test_en_past_dad_stroke_last_year(self):
        result = detect_emergency("My dad suffered a stroke last year")
        assert result is None

    # Kiireellisyyssignaalit estävät poisjätön → not None
    def test_urgency_cpr_right_now(self):
        result = detect_emergency("How do I perform CPR right now?")
        assert result is not None

    def test_urgency_fi_heti(self):
        result = detect_emergency("Kuinka elvytetään heti?")
        assert result is not None

    def test_urgency_en_help_me(self):
        result = detect_emergency("I am dying, please help me")
        assert result is not None
