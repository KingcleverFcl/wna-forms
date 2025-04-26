from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import SessionLocal
from app import models, auth, utils
from sqlalchemy.orm import Session

from fastapi.staticfiles import StaticFiles

models.Base.metadata.create_all(bind=models.engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Главная
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Вход
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.login == login).first()
    if not user or not auth.verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    response = RedirectResponse(url="/profile", status_code=302)
    response.set_cookie(key="user_login", value=user.login)
    return response

# Регистрация
@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
def register_post(request: Request, login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.login == login).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Login already taken"})
    hashed_password = auth.hash_password(password)
    new_user = models.User(login=login, password=hashed_password)
    db.add(new_user)
    db.commit()
    response = RedirectResponse(url="/profile", status_code=302)
    response.set_cookie(key="user_login", value=login)
    return response

# Профиль
@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, db: Session = Depends(get_db)):
    login = request.cookies.get("user_login")
    if not login:
        return RedirectResponse(url="/login")
    user = db.query(models.User).filter(models.User.login == login).first()
    forms = db.query(models.Form).filter(models.Form.creator == login).all()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "forms": forms})

# Создание формы
@app.get("/create-form", response_class=HTMLResponse)
def create_form_get(request: Request):
    login = request.cookies.get("user_login")
    if not login:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("create_form.html", {"request": request})

@app.post("/create-form", response_class=HTMLResponse)
def create_form_post(request: Request, total_questions: int = Form(...), total_answers: int = Form(...), db: Session = Depends(get_db)):
    login = request.cookies.get("user_login")
    if not login:
        return RedirectResponse(url="/login")
    link = utils.generate_random_link()
    new_form = models.Form(creator=login, total_questions=total_questions, total_answers=total_answers, link_form=link)
    db.add(new_form)

    user = db.query(models.User).filter(models.User.login == login).first()
    user.total_forms += 1

    db.commit()
    return RedirectResponse(url=f"/view-form/{link}", status_code=302)

# Просмотр формы
@app.get("/view-form/{link}", response_class=HTMLResponse)
def view_form(request: Request, link: str, db: Session = Depends(get_db)):
    form = db.query(models.Form).filter(models.Form.link_form == link).first()
    if not form:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("view_form.html", {"request": request, "form": form})

