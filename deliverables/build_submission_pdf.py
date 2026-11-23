import os
import subprocess
import base64
import time

def generate_pdf():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir)
    html_path = os.path.join(script_dir, "project_submission.html")
    
    out_pdf_deliverables = os.path.join(script_dir, "Project_Submission_UniAssist_AI.pdf")
    out_pdf_root = os.path.join(workspace_dir, "Project_Submission_UniAssist_AI.pdf")
    
    print(f"HTML source: {html_path}")
    
    # Try Method 1: Edge headless CLI directly (fast, no driver needed)
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
    ]
    
    edge_exe = None
    for p in edge_paths:
        if os.path.exists(p):
            edge_exe = p
            break
            
    success = False
    if edge_exe:
        print(f"Found Edge at: {edge_exe}")
        cmd = [
            edge_exe,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={out_pdf_deliverables}",
            f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=30)
            if os.path.exists(out_pdf_deliverables) and os.path.getsize(out_pdf_deliverables) > 1000:
                print(f"Successfully generated PDF via Edge CLI: {out_pdf_deliverables}")
                success = True
        except Exception as e:
            print(f"Edge CLI failed: {e}")
            
    # Try Method 2: Selenium Edge (used by original deliverables script)
    if not success:
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            from selenium.webdriver.common.print_page_options import PrintOptions
            
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1200,1600')
            driver = webdriver.Edge(options=options)
            try:
                abs_url = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
                driver.get(abs_url)
                time.sleep(1.5)
                
                print_options = PrintOptions()
                print_options.background = True
                print_options.margin_top = 0.6
                print_options.margin_bottom = 0.6
                print_options.margin_left = 0.6
                print_options.margin_right = 0.6
                
                pdf_b64 = driver.print_page(print_options)
                pdf_bytes = base64.b64decode(pdf_b64)
                with open(out_pdf_deliverables, "wb") as f:
                    f.write(pdf_bytes)
                print(f"Successfully generated PDF via Selenium: {out_pdf_deliverables}")
                success = True
            finally:
                driver.quit()
        except Exception as e:
            print(f"Selenium Edge failed: {e}")

    # Copy to root
    if success and os.path.exists(out_pdf_deliverables):
        with open(out_pdf_deliverables, "rb") as f_in:
            data = f_in.read()
        with open(out_pdf_root, "wb") as f_out:
            f_out.write(data)
        print(f"Also saved to workspace root: {out_pdf_root}")
        print(f"File size: {len(data)} bytes")
    else:
        print("Failed to generate PDF.")

if __name__ == "__main__":
    generate_pdf()
