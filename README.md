# CV Build Pipeline

This project generates an ATS-friendly, single-column PDF CV from structured data and style configurations.  
To customize or generate your CV, you need to provide the required input files in the `input/` folder.

---

## Input Folder Structure

The `input` folder must contain the following files:

### 1. CV Data Files

The CV data file contains all your personal and professional information.  
You may maintain multiple language versions, e.g.:

- `cv_data_en.json` – English version of your CV data
- `cv_data_fr.json` – French version of your CV data

**Example structure (cv_data_en.json):**
- `basics`: Name, professional title, profile, etc.
- `education`: Array of education entries
- `experience`: Array of work experience entries
- `languages`: Object of language proficiency
- `skills`: Array of skills
- `hobbies`: Array of hobbies

You may create other JSON files for additional languages or versions if needed.

### 2. Configuration File

- `config.json`

Defines style, layout, section order, fonts, colors, spacing, section titles, and output filename.  
You edit this file to change CV appearance or structure without touching your content data.

**Note:** The build script expects the configuration file to be located at `input/config.json`.

### 3. Secrets File

- `secrets.json`

This file provides sensitive details that should *not* be in version-controlled general data files:
  - `mail`
  - `phone`
  - `location`
These are automatically injected into your rendered CV, ensuring you keep sensitive data separate.

**Example:**
```json
{
    "mail": "youremail@example.com",
    "phone": "+12 345 678 900",
    "location": "Your City, Country"
}
```
---

## Input Folder Example

Your `input/` folder should look like this:

```
input/
 ├── config.json
 ├── secrets.json
 ├── cv_data_en.json
 ├── cv_data_fr.json
```

You can add additional files like `full_cv_en.json` for larger datasets or other backup versions, but only the files above are required by the default CV build script.

---

## Summary Table

| File              | Required | Purpose                                                                 |
|-------------------|----------|-------------------------------------------------------------------------|
| config.json       |   Yes    | Layout, fonts, colors, section order, output configuration, etc.         |
| secrets.json      |   Yes    | Contact information injected into the CV securely                        |
| cv_data_en.json   |   Yes*   | English CV data (replace `en` for other languages as needed)             |
| cv_data_fr.json   |   No*    | French CV data; used if generating French version                        |

*\*At least one language data file (e.g., `cv_data_en.json`) is required for CV generation.

---

## How To Customize

- **To update your CV content:** Edit the appropriate `cv_data_xx.json` file.
- **To change the CV's visual style:** Edit `config.json`.
- **To update your private contact info:** Edit `secrets.json`.

---

## Running The Script

Use the following command to generate a CV PDF (script will prompt for language):

```sh
python build_cv.py
```

Advanced usage (override defaults):

```sh
python build_cv.py --data input/cv_data_en.json --config input/config.json --out output/my_cv.pdf
```

---
