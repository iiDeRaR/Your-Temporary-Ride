from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "bugatti_ride_secret"

def get_db():
    conn = sqlite3.connect('rental.db')
    conn.row_factory = sqlite3.Row
    return conn
#Hompage route
@app.route('/')
def index():
    return render_template('index.html')

#Registration for both Cars and Customers this handles GET and POST methods too
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        reg_type = request.form.get('reg_type')
        #I used parameterized queries to prevent SQL injection
        try:
            if reg_type == 'car':
                db.execute("INSERT INTO cars (model, year, plate_id, price_per_day) VALUES (?, ?, ?, ?)",
                           (request.form['model'], request.form['year'], request.form['plate'], request.form['price']))
                flash("Car Registered Successfully!")
            else:
                db.execute("INSERT INTO customers (name, email) VALUES (?, ?)", 
                           (request.form['name'], request.form['email']))
                flash("Customer Registered Successfully!")
            db.commit()
        #Shows error message if duplicates are entered since plate_ID and name are PR keys
        except:
            flash("Error: Entry already exists (Plate ID or Name).")
    return render_template('register.html')
#shows all cars
@app.route('/cars')
def cars():
    db = get_db()
    all_cars = db.execute("SELECT * FROM cars").fetchall()
    return render_template('cars.html', cars=all_cars)

#Update car status manually if needed
@app.route('/update_status/<int:id>/<status>')
def update_status(id, status):
    db = get_db()
    db.execute("UPDATE cars SET status = ? WHERE id = ?", (status, id))
    db.commit()
    return redirect(url_for('cars'))

#Validate Name and Reserve procedure
@app.route('/reserve/<int:car_id>', methods=['GET', 'POST'])
def reserve(car_id):
    db = get_db()
    car = db.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
    if request.method == 'POST':
        name = request.form['customer_name']
        #I added this Match name in DB to check if the customer is registered
        check = db.execute("SELECT * FROM customers WHERE name = ?", (name,)).fetchone()
        if not check:
            flash(f"Error: '{name}' is not registered!")
            return redirect(url_for('reserve', car_id=car_id))
        
        db.execute("INSERT INTO reservations (customer_name, car_id, start_date, end_date) VALUES (?, ?, ?, ?)",
                   (name, car_id, request.form['start'], request.form['end']))
        db.execute("UPDATE cars SET status = 'rented' WHERE id = ?", (car_id,))
        db.commit()
        return redirect(url_for('reports'))
    return render_template('reserve.html', car=car)

#Automate Pickup, Return, and Payment
@app.route('/workflow/<int:res_id>/<action>')
def workflow(res_id, action):
    db = get_db()
    if action == 'pickup':
        db.execute("UPDATE reservations SET status = 'Picked Up' WHERE id = ?", (res_id,))
    elif action == 'return':
        #Get the reservation and the car's price per day
        res = db.execute("""
            SELECT r.start_date, r.end_date, c.price_per_day 
            FROM reservations r 
            JOIN cars c ON r.car_id = c.id 
            WHERE r.id = ?""", (res_id,)).fetchone()
        
        #Calculate the number of days
        fmt = '%Y-%m-%d'
        start = datetime.strptime(res['start_date'], fmt)
        end = datetime.strptime(res['end_date'], fmt)
        days = (end - start).days
        if days <= 0: days = 1 #I added this Minimum 1 day charge
        
        #Calculate total payment according to number of days entered
        total_price = days * res['price_per_day']
        
        #Update the database with the calculated price
        db.execute("UPDATE reservations SET status = 'Completed', payment = ? WHERE id = ?", (total_price, res_id))
        db.execute("UPDATE cars SET status = 'active' WHERE id = (SELECT car_id FROM reservations WHERE id = ?)", (res_id,))
    
    db.commit()
    return redirect(url_for('reports'))

@app.route('/reports')
def reports():
    db = get_db()
    #Gets all reservations made (past and present)
    res = db.execute("SELECT r.*, c.model FROM reservations r JOIN cars c ON r.car_id = c.id").fetchall()
    #Shows all registered customers
    all_customers = db.execute("SELECT * FROM customers").fetchall()
   
    return render_template('reports.html', reservations=res, customers=all_customers)

#Route to delete a customer
@app.route('/delete_customer/<int:id>')
def delete_customer(id):
    db = get_db()
    db.execute("DELETE FROM customers WHERE id = ?", (id,))
    db.commit()
    flash("Customer record removed.")
    return redirect(url_for('reports'))

#Route to update customer's email
@app.route('/update_customer_email/<int:id>', methods=['POST'])
def update_customer_email(id):
    new_email = request.form.get('new_email')
    db = get_db()
    db.execute("UPDATE customers SET email = ? WHERE id = ?", (new_email, id))
    db.commit()
    flash("Customer email updated!")
    return redirect(url_for('reports'))

#Route to delete a car from the fleet
@app.route('/delete_car/<int:id>')
def delete_car(id):
    db = get_db()
    db.execute("DELETE FROM cars WHERE id = ?", (id,))
    db.commit()
    flash("Car removed from fleet.")
    return redirect(url_for('cars'))

#Route to update a car's price
@app.route('/update_price/<int:id>', methods=['POST'])
def update_price(id):
    new_price = request.form.get('new_price')
    db = get_db()
    db.execute("UPDATE cars SET price_per_day = ? WHERE id = ?", (new_price, id))
    db.commit()
    flash("Price updated successfully!")
    return redirect(url_for('cars'))

if __name__ == '__main__':
    app.run(debug=True)