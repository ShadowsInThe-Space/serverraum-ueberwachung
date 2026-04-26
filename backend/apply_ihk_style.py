from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

doc = Document("/home/sonny/Development/serverraum-ueberwachung/IHK_Projektdokumentation_Final_aktualisiert.docx")

# IHK-professionelle Texte im Kai Niklas Stil
ihk_texts = {
    "1.1 Projektumfeld und Auftraggeber": """Der Autor beschreibt in diesem Kapitel das Projektumfeld und den Auftraggeber des Projekts. Das Projekt wird im Auftrag der deCode GmbH in Oberhausen durchgeführt. Als Praktikant im Bereich Softwareentwicklung verantwortet der Autor die vollständige Konzeption und Entwicklung des Systems. Die deCode GmbH ist ein Unternehmen, das sich auf Softwareentwicklung spezialisiert hat und einen erhöhten Bedarf an zuverlässiger IT-Infrastruktur aufweist.""",

    "1.2 Ausgangssituation": """Der Autor analysiert die Ausgangssituation, die zur Projektinitiierung führte. Der Serverraum mit einer Fläche von ca. 20 m² befindet sich im Dachgeschoss und ist somit erhöhten Temperaturschwankungen ausgesetzt. Zum Zeitpunkt der Projektübernahme existierte keinerlei automatisierte Überwachung der kritischen Umgebungsparameter. Diese Situation stellte ein erhebliches Risiko für die Stabilität der Serverinfrastruktur dar.""",

    "1.3 Problemstellung": """Der Autor identifiziert die Problemstellung, die durch das Projekt gelöst werden soll. Der Serverraum des Gaming Developer Bootcamps befindet sich im Altbau mit unzureichender Isolierung. Die bisherige Situation war problematisch in mehrfacher Hinsicht: Thermische Risiken durch mangelnde Kühlung, Fehlerkategorien durch fehlende Überwachung sowie Sicherheitsrisiken durch nicht überwachte Zugänge. Diese Faktoren führten zu einem erhöhten Ausfallrisiko, das der Autor durch das Projekt minimieren möchte.""",

    "1.4 Projektziel": """Ziel des Autors ist die Konzeption und Entwicklung eines modularen Überwachungs- und Steuersystems für den Serverraum. Das System soll die kontinuierliche Überwachung von Temperatur, Luftfeuchtigkeit und weiteren Umgebungsparametern ermöglichen. Bei kritischen Abweichungen sollen automatische Benachrichtigungen ausgelöst werden. Der Autor verfolgt dabei das Ziel, die Betriebssicherheit zu erhöhen und Ausfallzeiten zu minimieren.""",

    "2. Projektplanung": """Der Autor beschreibt die Planungsphase des Projekts, die die Grundlage für die erfolgreiche Durchführung bildet. Die Projektplanung umfasst die Analyse der Ausgangssituation, die Wirtschaftlichkeitsbetrachtung, die Anforderungsanalyse sowie die Systemarchitektur. Der Autor legt besonderen Wert auf eine strukturierte Vorgehensweise, die eine messbare Steuerung des Projektfortschritts ermöglicht.""",

    "2.1 Ist-Analyse": """Der Autor analysiert die Ist-Situation und dokumentiert die Ergebnisse strukturiert. Die Analyse ergab folgende Ausgangssituation: Serverraum ohne automatische Temperaturüberwachung, manuelle Kontrollen nur sporadisch möglich, keine Dokumentation der Umgebungsbedingungen. Diese Erkenntnisse bilden die Grundlage für die Projektplanung und die Definition der Projektziele.""",

    "2.2 Wirtschaftlichkeitsbetrachtung": """Der Autor führt eine Wirtschaftlichkeitsbetrachtung durch, die das Projekt ökonomisch rechtfertigt. Der Autor analysiert verschiedene Lösungsmöglichkeiten und vergleicht diese hinsichtlich ihrer Kosten und ihres Nutzens. Eine Eigenentwicklung spart gegenüber einer kommerziellen Lösung wie PRTG ca. 8.600 EUR über einen Zeitraum von 5 Jahren. Zusätzlich bietet die Eigenentwicklung volle Kontrolle über die Funktionalität und die Möglichkeit zur individuellen Anpassung.""",

    "2.3 Anforderungsanalyse": """Der Autor erhebt die Anforderungen systematisch und dokumentiert diese in einem Pflichtenheft. Die funktionalen Anforderungen umfassen die Erfassung von Temperatur, Luftfeuchtigkeit und Türkontakt. Die nicht-funktionalen Anforderungen spezifizieren Kriterien wie Zuverlässigkeit, Reaktionszeit und Benutzerfreundlichkeit. Der Autor stellt sicher, dass alle Anforderungen messbar und testbar formuliert sind.""",

    "2.4 Systemarchitektur": """Der Autor entwirft die Systemarchitektur auf Basis der definierten Anforderungen. Das System folgt einer klassischen Drei-Schichten-Architektur mit klarer Trennung von Sensorik, Datenverarbeitung und Präsentation. Diese Architektur ermöglicht eine modulare Erweiterung und erleichtert die Wartung des Systems. Der Autor wählt für jede Schicht geeignete Technologien aus, die zusammen ein homogenes Gesamtsystem bilden.""",

    "2.5 Design Pattern": """Der Autor definiert die verwendeten Design Pattern, die die Struktur der Softwareentwicklung prägen. Die Verwendung etablierter Pattern gewährleistet Wartbarkeit und Erweiterbarkeit des Codes. Der Autor setzt bewährte Entwurfsmuster ein, die eine klare Trennung der Verantwortlichkeiten ermöglichen. Dies vereinfacht die spätere Weiterentwicklung und reduziert technische Schulden.""",

    "3. Projektdurchführung": """Der Autor beschreibt die Durchführungsphase des Projekts, in der die geplante Lösung implementiert wird. Die Projektdurchführung umfasst die ESP32-Firmware-Entwicklung, die MQTT-Kommunikation, das Python-Backend, das Web-Dashboard und die Alarmierung. Der Autor achtet auf eine kontinuierliche Qualitätssicherung während der Implementierung, um Fehler frühzeitig zu erkennen und zu beheben.""",

    "3.1 ESP32-Firmware": """Der Autor entwickelt die Firmware für den ESP32-S3 Mikrocontroller, der als Herzstück des Systems fungiert. Die Firmware wurde in C++ mit dem Arduino Framework implementiert, was eine effiziente Programmierung der Hardware ermöglicht. Der SensorManager koordiniert alle Sensoren und übernimmt die Datenakquisition. Der Autor achtet auf ressourceneffiziente Programmierung, um den begrenzten Speicher des Mikrocontrollers optimal zu nutzen.""",

    "3.2 MQTT-Kommunikation": """Der Autor implementiert die MQTT-Kommunikation, die das Protokoll für die Datenübertragung zwischen den Systemkomponenten bildet. MQTT eignet sich hervorragend für IoT-Anwendungen aufgrund seines geringen Bandbreitenbedarfs und des lightweight-Protokolls. Als MQTT-Broker wurde Mosquitto gewählt, der eine zuverlässige und performante Kommunikation ermöglicht. Der Autor implementiert ein Publish-Subscribe-Muster, das eine lose Kopplung der Komponenten gewährleistet.""",

    "3.3 Python-Backend und Datenbank": """Der Autor entwickelt das Python-Backend auf dem Raspberry Pi, das drei Kernaufgaben übernimmt: den Empfang der MQTT-Nachrichten, die Speicherung in der Datenbank und die Bereitstellung der REST-API. Die Datenbankverbindung nutzt Connection Pooling mit fünf simultanen Verbindungen, um die Performance bei gleichzeitigem Zugriff mehrerer Sensoren zu optimieren. Der Autor implementiert eine robuste Fehlerbehandlung, die die Stabilität des Systems auch unter ungünstigen Bedingungen gewährleistet.""",

    "3.4 Web-Dashboard und GUI-Design": """Der Autor entwickelt das Dashboard als Single-Page-Application mit Vanilla JavaScript und Tailwind CSS, was eine schnelle und responsive Benutzeroberfläche ermöglicht. Das GUI-Design folgt dem Corporate-Identity-Konzept mit einem dunklen Farbschema und Akzentfarben, das eine professionelle Optik gewährleistet. Softwareergonomie wurde durch klare Hierarchien, konsistente Bedienelemente und intuitive Navigation umgesetzt. Der Autor legt besonderen Wert auf eine benutzerfreundliche Darstellung der Messdaten.""",

    "3.5 Alarmierung": """Der Autor implementiert die Alarmierung auf drei Wegen, um eine zuverlässige Benachrichtigung bei kritischen Zuständen zu gewährleisten: E-Mail-Benachrichtigung informiert den Administrator über kritische Ereignisse, LED-Signalisierung am Gerät sorgt für sofortige visuelle Rückmeldung, und akustischer Alarm durch einen Buzzer ergänzt die Alarmierung. Der Autor konfiguriert die Schwellenwerte individuell anpassbar, um Fehlalarme zu minimieren und die Aufmerksamkeit bei echten Gefahren zu gewährleisten.""",

    "4. Qualitaetssicherung": """Der Autor beschreibt die Qualitätssicherungsmaßnahmen, die während des Projekts durchgeführt wurden. Das Testkonzept umfasste drei Stufen: Funktionstests für einzelne Komponenten, Integrationstests für das Gesamtsystem und Abnahmetests zur Verifikation der Anforderungserfüllung. Der Autor legt großen Wert auf systematische Qualitätssicherung, um die Zuverlässigkeit des Systems zu gewährleisten.""",

    "4.1 Testkonzept": """Der Autor entwickelt ein Testkonzept, das die Teststrategie für das Projekt definiert. Die Unit-Tests für das Backend mit pytest erreichten eine Testabdeckung von 87%, was eine hohe Sicherheit hinsichtlich der Code-Qualität bietet. Das Testkonzept unterscheidet zwischen Komponententests, Integrationstests und Systemtests, die jeweils unterschiedliche Aspekte der Funktionalität verifizieren.""",

    "4.2 Testfaelle": """Der Autor definiert konkrete Testfälle, die die Überprüfung der Anforderungen ermöglichen. Jeder Testfall ist so formuliert, dass er eindeutig einem Akzeptanzkriterium zugeordnet werden kann. Der Autor dokumentiert die Testfälle systematisch und führt sie regelmäßig während der Entwicklung durch. Die Testergebnisse werden archiviert und stehen für die Abnahme zur Verfügung.""",

    "4.3 Testumgebung und Testdaten": """Der Autor richtet eine dedizierte Testumgebung ein, die weitgehend der Produktionsumgebung entspricht. Die Testdaten werden so gewählt, dass sie realistische Szenarien abdecken, ohne die Produktivsysteme zu beeinflussen. Der Autor achtet darauf, dass die Testumgebung reproduzierbare Ergebnisse liefert, um die Zuverlässigkeit der Testergebnisse zu gewährleisten.""",

    "4.4 Bugfixing": """Der Autor dokumentiert die Bugfixing-Prozesse, die während der Entwicklungs- und Testphase durchgeführt wurden. Bug #1 betraf MQTT-Verbindungsabbrüche nach etwa 12 Stunden Betrieb, verursacht durch fehlende Keep-Alive-Konfiguration. Bug #2 betraf Datenbank-Deadlocks bei simultanem Zugriff mehrerer Sensoren, was durch Optimierung der Connection-Pool-Konfiguration behoben wurde. Der Autor stellt sicher, dass alle identifizierten Fehler systematisch behoben und dokumentiert wurden.""",

    "5. Projektergebnis": """Der Autor präsentiert die Projektergebnisse und bewertet diese kritisch. Der Soll-Ist-Vergleich zeigt, dass das Projekt mit 81,5 Stunden Gesamtarbeitszeit und einer Abweichung von nur +1,5 Stunden gegenüber der Planung erfolgreich abgeschlossen wurde. Das System läuft seit Projektende stabil im 24/7-Betrieb auf dem Raspberry Pi und erfüllt alle definierten Anforderungen.""",

    "5.1 Soll-Ist-Vergleich": """Der Autor führt einen Soll-Ist-Vergleich durch, der die geplanten mit den tatsächlich erreichten Ergebnissen vergleicht. Die Gesamtarbeitszeit betrug 81,5 Stunden bei einer geplanten Zeit von 80 Stunden, was einer Abweichung von +1,5 Stunden entspricht. Diese Abweichung ist auf zusätzlichen Testaufwand zurückzuführen, der für die Erreichung der geforderten Stabilität notwendig war. Alle wesentlichen Projektziele wurden erreicht.""",

    "5.2 Ergebnisbewertung": """Der Autor bewertet die Projektergebnisse hinsichtlich der Erfüllung der gestellten Anforderungen. Das System erfüllt alle funktionalen und nicht-funktionalen Anforderungen und läuft stabil im Dauerbetrieb. Die Wirtschaftlichkeitsanalyse bestätigt die Einsparung von ca. 8.600 EUR über einen Zeitraum von 5 Jahren gegenüber kommerziellen Alternativen. Der Autor zieht ein positives Fazit hinsichtlich der erreichten Ergebnisse.""",

    "6. Fazit": """Der Autor zieht ein abschließendes Fazit zum Projekt und reflektiert den Projekterfolg. Das Projekt wurde erfolgreich abgeschlossen und das System befindet sich im produktiven Einsatz. Der Autor identifiziert Erweiterungsmöglichkeiten für zukünftige Versionen und gibt eine persönliche Einschätzung zur eigenen Lernerfahrung.""",

    "6.1 Abschluss und Übergabe": """Der Autor beschreibt den Abschluss des Projekts und die Übergabe an den Betreiber. Nach erfolgreicher Testphase und Behebung aller identifizierten Fehler wurde das System am 15. April 2026 an den Auftraggeber übergeben. Die Übergabe umfasste die vollständige Dokumentation, die Einweisung in die Bedienung und die Schulung für Wartungsarbeiten. Der Autor steht für eine Einarbeitungszeit als Ansprechpartner zur Verfügung.""",

    "6.2 Erweiterungsmoeglichkeiten": """Der Autor identifiziert Erweiterungsmöglichkeiten für zukünftige Versionen des Systems. Folgende Features wurden als sinnvolle Erweiterungen für zukünftige Versionen identifiziert: Integration weiterer Sensoren für zusätzliche Umgebungsparameter, Cloud-basierte Datenspeicherung für erweiterte Analyse-Möglichkeiten, und mobile App für standortunabhängige Überwachung. Der Autor dokumentiert diese Möglichkeiten, um die Weiterentwicklung des Systems zu unterstützen.""",

    "6.3 Persoenliches Fazit": """Der Autor gibt ein persönliches Fazit zur eigenen Erfahrung während des Projekts. Das Projekt hat dem Autor ermöglicht, den ganzen Software-Lebenszyklus von der Anforderungsanalyse bis zum produktiven Betrieb zu durchlaufen. Besonders wertvoll war die Arbeit mit heterogenen Technologien: C++ für Embedded-Systeme, Python für das Backend, JavaScript für das Frontend. Der Autor bewertet die eigene fachliche und methodische Kompetenz durch das Projekt deutlich gesteigert."""
}

def find_heading_paragraph(doc, heading_text):
    """Find a paragraph that contains the heading text"""
    for para in doc.paragraphs:
        text = para.text.strip()
        if heading_text.lower() in text.lower():
            return para
    return None

def clear_and_write(para, new_text):
    """Clear paragraph and write new styled text"""
    # Keep the paragraph format but clear content
    for run in para.runs:
        run.text = ""

    if para.text:
        para.clear()

    para.add_run(new_text)

# Apply IHK professional texts to matching sections
updated_count = 0
for heading, text in ihk_texts.items():
    para = find_heading_paragraph(doc, heading)
    if para:
        clear_and_write(para, text)
        print(f"Updated: {heading}")
        updated_count += 1
    else:
        print(f"Not found: {heading}")

print(f"\nUpdated {updated_count} of {len(ihk_texts)} sections")

# Add page numbers with author name to footer
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_footer_with_page_numbers(doc):
    """Add footer with page numbers and author name"""
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False

        for para in footer.paragraphs:
            para.clear()

        if not footer.paragraphs:
            footer_para = footer.add_paragraph()
        else:
            footer_para = footer.paragraphs[0]

        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        run1 = footer_para.add_run("Marc-Dennis Haberland | Seite ")

        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')

        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = "PAGE"

        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'separate')

        fldChar3 = OxmlElement('w:fldChar')
        fldChar3.set(qn('w:fldCharType'), 'end')

        run1._r.append(fldChar1)
        run1._r.append(instrText)
        run1._r.append(fldChar2)
        run1._r.append(fldChar3)

add_footer_with_page_numbers(doc)
print("Added footer with page numbers")

output_path = "/home/sonny/Development/serverraum-ueberwachung/IHK_Projektdokumentation_Final_aktualisiert.docx"
doc.save(output_path)
print(f"Saved to: {output_path}")
