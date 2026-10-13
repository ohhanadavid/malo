# Task Brief — Full Bilingual Translation

This is a full, literal, paragraph-by-paragraph translation of the original Hebrew task brief `task/תרגיל.docx` into English, for reference during implementation. Each original line/paragraph is given first (in a blockquote), immediately followed by its English translation. The translation is intentionally literal — it does not summarize, resolve ambiguity, or add interpretation beyond the source text.

For the condensed, structured/interpreted version of this task (used for planning and implementation), see `CLAUDE.md` in the project root.

---

## Goal statement

> מטרת המשימה היא לחשב שיעורי השבה בית ספריים / ארציים

The goal of the task is to calculate school-level / national-level response rates (שיעורי השבה).

> לצורך המענה, אנא כתבו קוד באחת מהתוכנות R או Python. הקפידו לשמור את קובץ הסינטקסט

For the purpose of the response, please write code in one of the programs R or Python. Make sure to keep/save the syntax file.

---

## Available files

> לרשותכם עומדים כמה קבצים רלוונטיים:

At your disposal are several relevant files:

> קובץ נתונים "All data" - שמכיל כמה גיליונות ( את כל הנוסחים כולל  "varnames ")

A data file "All data" - which contains several sheets (all of the forms, including "varnames").

> "varnames" - פירוט השאלות בכל אחד מנוסחי המבחן

"varnames" - a detailing of the questions in each one of the test's forms.

> קובץ בשם "sppop"  - בעלי צרכים מיוחדים

A file named "sppop" - [those with] special needs.

> קובץ בשם "schools"  - טבלה המרכזת את בתי ספר כולל מאפייני רקע.

A file named "schools" - a table that consolidates the schools, including background characteristics.

> טבלאות תרגום שיאפשרו לכם להבין את הקידודים עבור מגזר ופיקוח.

Translation tables that will allow you to understand the codings for sector (מגזר) and supervision (פיקוח).

---

## Steps for carrying out the task

> שלבים לביצוע המשימה

Steps for carrying out the task.

> לפני שמתחילים יש לקרוא את כל הסעיפים

Before starting, one must read all of the sections.

### Step 1 — identifying blank notebooks

> זיהוי מחברות ריקות: יש להוסיף עמודה בשם cntvalid  לכל אחד מקבצי הנתונים. עמודה זו תחושב בהתאם למספר התשובות שענה התלמיד במבחן ( ערכים 98 ו 99 לא נחשבים ערכים קבילים). יש לספור רק שאלות שמקבלות ערך 1 בשדה Ind1 בטבלת varnames.  יש לבנות לולאה שתרוץ על כל אחד מהנוסחים ותעדכן את השדה הנ"ל בהתאם.

Identifying blank notebooks/booklets: a column named cntvalid must be added to each one of the data files. This column will be calculated according to the number of answers that the student answered on the test (values 98 and 99 are not considered acceptable values). Only questions that receive a value of 1 in the Ind1 field in the varnames table should be counted. A loop must be built that will run over each one of the forms and update the aforementioned field accordingly.

### Step 2 — classifying students in the special needs file

> סיווג תלמידים בקובץ צרכים מיוחדים.  ( רגיל, עולה חדש, משולב, עולה ותיק).

Classifying students in the special needs file. (regular, new immigrant, combined/integrated, veteran immigrant).

> יש לעשות זאת ע"י עדכון שדה pop_id בטבלה בהתאם לקבוצה ולסטטוס של התלמיד (ראה טבלת קידוד בהמשך)

This should be done by updating the pop_id field in the table according to the group and the status of the student (see the coding table further below).

> קבוצה 1 עם סטטוס 200 (ברירת מחדל) – עולה חדש

Group 1 with status 200 (default) – new immigrant.

> קבוצה 1עם סטטוס 400 – עולה ותיק

Group 1 with status 400 – veteran immigrant.

> קבוצה 2 עם סטטוס 400 (ברירת מחדל) – עולה וותיק

Group 2 with status 400 (default) – veteran immigrant.

> קבוצה 2 עם סטטוס 200 – עולה חדש

Group 2 with status 200 – new immigrant.

> קבוצות 5 ו 6 עם סטטוס 400 (ברירת מחדל) - משולב

Groups 5 and 6 with status 400 (default) - combined/integrated.

> קבוצות 5 ו 6 עם סטטוס 200/ 300– במידה והגיע להיבחן ( cntvalid>0) יהפוך לסטטוס 400 ויטופל בהתאם. במידה ולא הגיע יש לסמן אותו בעמודה del  בערך 2.

Groups 5 and 6 with status 200/300 – in case he arrived to be tested (cntvalid>0), he will turn into status 400 and will be handled accordingly. In case he did not arrive, he should be marked in the column del with the value 2.

> סטטוס 100 – תלמיד רגיל ברמה הבית ספרית . אולם ברמה הארצית יסווג בהתאם לקבוצה ולסטטוס ברירת המחדל שלה.

Status 100 – a regular student at the school level. However, at the national level he will be classified according to the group and its default status.

> סטטוס 700 – תלמיד רגיל

Status 700 – a regular student.

> סטטוס 600 – במידה והגיע להיבחן   (cntvalid >0)יש לסווג בהתאם לקבוצה ולסטטוס ברירת המחדל שלה. במידה ולא הגיע יש למחוק אותו מקובץ צרכים מיוחדים ( לצורך העניין יסומן ב del=1 ).

Status 600 – in case he arrived to be tested (cntvalid>0), he should be classified according to the group and its default status. In case he did not arrive, he should be deleted from the special needs file (for this purpose he will be marked with del=1).

### Coding table

> טבלת קידוד צרכים מיוחדים:

Special needs coding table:

| desc (Hebrew) | desc (English) | pop_id |
|---|---|---|
| רגיל | regular | 0 |
| עולה חדש | new immigrant | 4 |
| משולב | combined/integrated | 6 |
| עולה ותיק | veteran immigrant | 7 |

> משתנה pop_id_n  (רמה ארצית ) יקבל את אותם ערכים כמו pop_id (בית ספרי ) מלבד מקרים בהם מדובר בסטטוס 100 (ראה טיפול לעיל).

The variable pop_id_n (national level) will receive the same values as pop_id (school-level), except for cases in which it concerns status 100 (see the handling above).

### Step 3 — building TblAllTest

> יש ליצור data set חדש בשם TblAllTest המכיל את כלל התלמידים מכל  הנוסחים עם השדות הבאים:
> ת"ז, סמל בית ספר, מקבילה, קוד שאלון,  סידורי שאלון ו cntvalid בנוסף יש לצרף את השדות הבאים: מגזר, פיקוח, מחוז ( יש לעדכן אותם מקובץ בתי ספר).

A new data set named TblAllTest must be created, containing all of the students from all of the forms with the following fields:
ID number (ת"ז), school symbol, parallel, questionnaire code, questionnaire serial, and cntvalid. In addition, the following fields must be attached: sector (מגזר), supervision (פיקוח), district (מחוז) (these should be updated from the schools file).

### Step 4 — delcodeb

> לאחר מכן יש להוסיף משתנה delcodeb. המשתנה יקבל ערכים זהים ל pop_id אך במידה ומדובר במחברת ריקה יקבל בכל מקרה ערך 5. נבחנים שלא מופיעים בקובץ צרכים מיוחדים יסווגו כרגילים. כנ"ל לגביי delcodeb_n בהתאם ל pop_id_n.

After that, a variable delcodeb must be added. The variable will receive values identical to pop_id, but in case it concerns a blank notebook, it will in any case receive the value 5. Test-takers who do not appear in the special needs file will be classified as regular. The same applies regarding delcodeb_n, according to pop_id_n.

### Step 5 — calculating the national norm count

> יש לחשב את מספר הנבחנים עבור הנורמה הארצית. ( ללא חרדים, ללא *מז"י, ללא עולים חדשים, ללא מחברות ריקות.) כמו כן יש להוציא החוצה תלמידים  שנבחנו **בנוסח אשר אינו תואם את האוכלוסייה שלהם. (דוברי ערבית שנבחנו בנוסח עברית ולהיפך. כנ"ל חרדים שנבחנו בנוסח שאינו חרדי ולהיפך).

The number of test-takers for the national norm must be calculated. (Without Haredim, without *M.Y. [מז"י], without new immigrants, without blank notebooks.) Likewise, students who were tested in **a form that does not match their population must be taken out. (Arabic speakers who were tested in a Hebrew form and vice versa. The same for Haredim who were tested in a form that is not Haredi, and vice versa.)

### Step 6 — list of schools

> יש להציג רשימה של בתי ספר שפרופורציית הנבחנים בעלי צרכים מיוחדים שלהם הוא מעל 20% ובנוסף מספר הנבחנים הרגילים שלהם גדול מ 15 (לצורך החישוב יש להתעלם מעולים חדשים ומחברות ריקות)

A list of schools must be presented whose proportion of test-takers with special needs is above 20%, and in addition the number of their regular test-takers is greater than 15 (for the purpose of the calculation, new immigrants and blank notebooks should be ignored).

---

## Footnotes

> *מז"י – מזרח ירושלים, מגזר ערבי במחוז 13

*M.Y. (מז"י) – East Jerusalem, Arab sector in district 13.

> ** הספרה השלישית בקוד שאלון מתארת את אוכלוסיית היעד של הנוסח.

**The third digit in the questionnaire code describes the target population of the form.
