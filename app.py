from flask import Flask, render_template, request, redirect, url_for, session
import os
from collections import Counter

app = Flask(__name__)
app.secret_key = "your_secret_key_here" 

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Login page route
@app.route("/")
def login():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


@app.route("/file-verification", methods=["GET", "POST"])
def file_verification():
    result = None

    if request.method == "POST":
        f1 = request.files.get("file1")
        f2 = request.files.get("file2")
    
        if not f1 or not f2:
            result = {"status": "error", "message": "Both files required"}
        else:
            p1 = os.path.join(app.config["UPLOAD_FOLDER"], f1.filename)
            p2 = os.path.join(app.config["UPLOAD_FOLDER"], f2.filename)
            f1.save(p1)
            f2.save(p2)

            try:
                from compare_two_files import compare_files
                
                matched = compare_files(p1, p2, debug=True)
                
                try:
                    os.remove(p1)
                    os.remove(p2)
                except:
                    pass
                
                if matched:
                    result = {
                        "status": "success", 
                        "message": "✅ FILES MATCH PERFECTLY",
                        "match": True
                    }
                else:
                    result = {
                        "status": "fail", 
                        "message": "❌ FILES DO NOT MATCH",
                        "match": False
                    }
                    
            except Exception as e:
                try:
                    os.remove(p1)
                    os.remove(p2)
                except:
                    pass
                
                result = {
                    "status": "error", 
                    "message": f"Error processing files: {str(e)}",
                    "match": False
                }

    # ✅ IMPORTANT: ALWAYS RETURN THE TEMPLATE
    return render_template("file_verification.html", result=result)


@app.route("/character-enclose", methods=["GET", "POST"])
def character_enclose():
    result = None
    input_text = ""

    if request.method == "POST":
        input_text = request.form.get("input_text", "")

        values = [
            v.strip()
            for v in input_text.replace(",", "\n").splitlines()
            if v.strip()
        ]

        result = ", ".join(f'"{v}"' for v in values)

    # ✅ IMPORTANT: ALWAYS RETURN THE TEMPLATE
    return render_template(
        "character_enclose.html",
        result=result,
        input_text=input_text
    )


@app.route("/subsidiary-compare", methods=["GET", "POST"])
def subsidiary_compare():
    result = None

    def normalize_values(text):
        if not text:
            return []
        parts = text.replace(",", " ").split()
        return [p.strip().lower() for p in parts if p.strip()]

    values = {
        "val1": "",
        "val2": "",
        "val3": "",
        "val4": "",
        "val5": "",
    }

    if request.method == "POST":
        for k in values:
            values[k] = request.form.get(k, "")

        filled_lists = [
            normalize_values(v)
            for v in values.values()
            if v.strip()
        ]

        if len(filled_lists) < 2:
            result = {
                "status": "error",
                "message": "Please enter at least 2 text boxes"
            }
        else:
            reference = filled_lists[0]
            mismatches = []

            idx = 1
            for v in values.values():
                if v.strip():
                    current = normalize_values(v)
                    
                    if reference != current:
                        ref_counter = Counter(reference)
                        curr_counter = Counter(current)
                        
                        missing = []
                        extra = []
                        
                        for item, count in ref_counter.items():
                            curr_count = curr_counter.get(item, 0)
                            if curr_count < count:
                                missing.extend([item] * (count - curr_count))
                        
                        for item, count in curr_counter.items():
                            ref_count = ref_counter.get(item, 0)
                            if ref_count < count:
                                extra.extend([item] * (count - ref_count))
                        
                        if missing or extra:
                            mismatches.append({
                                "column": f"Textbox {idx}",
                                "missing": sorted(missing),
                                "extra": sorted(extra)
                            })
                idx += 1

            if not mismatches:
                result = {
                    "status": "success",
                    "message": "✅ VALUES MATCH"
                }
            else:
                result = {
                    "status": "fail",
                    "message": "❌ VALUES DO NOT MATCH",
                    "details": mismatches
                }

    # ✅ IMPORTANT: ALWAYS RETURN THE TEMPLATE
    return render_template(
        "subsidiary_compare.html",
        result=result,
        values=values
    )

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
