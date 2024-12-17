import sys
import psycopg2
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QMessageBox, QLineEdit, QLabel


class DatabaseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Автосервис - Запросы к БД")
        self.resize(800, 600)

        self.layout = QVBoxLayout()


        self.query_button = QPushButton("Получить стоимость услуг для клиентов")
        # Поле ввода для ID машины
        self.car_id_label = QLabel("Введите ID машины:")
        self.car_id_input = QLineEdit()
        self.query_button_services = QPushButton("Получить список услуг")
        self.query_button_cars = QPushButton("Машины на обслуживании")
        self.query_button_car_info = QPushButton("Информация о машине (услуги)")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        # Добавляем элементы на форму

        self.layout.addWidget(self.query_button_services)
        self.layout.addWidget(self.query_button_cars)
        self.layout.addWidget(self.query_button)
        self.layout.addWidget(self.car_id_label)
        self.layout.addWidget(self.car_id_input)
        self.layout.addWidget(self.query_button_car_info)
        self.layout.addWidget(self.output)
        self.setLayout(self.layout)

        # Подключаем кнопки к обработчикам
        self.query_button.clicked.connect(self.calculate_total_cost)
        self.query_button_services.clicked.connect(self.get_services)
        self.query_button_cars.clicked.connect(self.get_cars_on_service)
        self.query_button_car_info.clicked.connect(self.get_car_services)

    def get_services(self):
        try:
            # Подключение к базе данных
            connection = psycopg2.connect(
                dbname="autoservice",
                user="postgres",
                password="2463",
                host="localhost",
                port="5432"
            )
            cursor = connection.cursor()

            # Выполняем запрос
            query = "SELECT name, base_price FROM services;"
            cursor.execute(query)
            services = cursor.fetchall()

            # Отображаем результаты
            self.output.clear()
            for name, base_price in services:
                self.output.append(f"Услуга: {name}, Цена: {base_price} руб.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить запрос: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

    def get_cars_on_service(self):
            try:
                conn = psycopg2.connect(
                    dbname="autoservice",
                    user="postgres",
                    password="2463",
                    host="localhost",
                    port="5432"
                )
                cur = conn.cursor()
                cur.execute("SELECT id, model FROM car WHERE on_service = TRUE;")
                cars = cur.fetchall()
                self.output.clear()
                self.output.append("Машины на обслуживании:\n")
                if cars:
                    for car in cars:
                        self.output.append(f"ID: {car[0]}, Модель: {car[1]}")
                else:
                    self.output.append("Нет машин на обслуживании.")
                cur.close()
                conn.close()
            except Exception as e:
                self.output.setText(f"Ошибка: {e}")


    def get_services_total(self, id):
        car_id = id
        conn = psycopg2.connect(
            dbname="autoservice",
            user="postgres",
            password="2463",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(s.base_price) AS total_price
            FROM car c
            JOIN orders_details od ON c.id = od.car_id
            JOIN services s ON od.service_id = s.id
            WHERE c.id = %s;
        """, (car_id,))

        result = cursor.fetchone()  # Получаем результат
        if result:
            total_price = result[0]  # Получаем сумму из первого столбца
            self.output.append(f"Сумма услуг для машины с ID {car_id}: {total_price} рублей")
        else:
            self.output.append("Услуги для указанной машины не найдены.")

        cursor.close()
        conn.close()



    def get_car_services(self):
        car_id = self.car_id_input.text().strip()
        if not car_id.isdigit():
            self.output.setText("Ошибка: Введите корректный ID машины (число).")
            return

        query = """
        SELECT c.id AS car_id,
               c.model AS car_model,
               s.name AS service_name,
               s.base_price,
               SUM(s.base_price) OVER (PARTITION BY c.id) AS total_price
        FROM car c
        JOIN orders_details od ON c.id = od.car_id
        JOIN services s ON od.service_id = s.id
        WHERE c.id = %s;
        """
        try:
            conn = psycopg2.connect(
                dbname="autoservice",
                user="postgres",
                password="2463",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()
            cur.execute(query, (car_id,))
            results = cur.fetchall()

            self.output.clear()
            if results:
                self.output.append(f"Информация о машине ID {car_id}, модель {results[0][1]}:\n")
                for row in results:
                    self.output.append(f"Услуга: {row[2]}, Цена: {row[3]}")
                self.get_services_total(car_id)
            else:
                self.output.append(f"Нет информации об услугах для машины ID {car_id}.")
            cur.close()
            conn.close()
        except Exception as e:
            self.output.setText(f"Ошибка: {e}")



    def calculate_total_cost(self):
            connection = psycopg2.connect(
            dbname="autoservice",
            user="postgres",
            password="2463",
            host="localhost",
            port="5432"
            )
            cursor = connection.cursor()

            # Запрос для расчета стоимости услуг для клиента
            cursor.execute("""
                SELECT
                    cl.name AS client_name,
                    SUM(s.base_price) AS total_services_cost
                FROM
                    client cl
                JOIN
                    car c ON cl.id = c.client_id
                JOIN
                    orders_details od ON c.id = od.car_id
                JOIN
                    services s ON od.service_id = s.id
                GROUP BY
                    cl.name;
            """)

            result = cursor.fetchall()  # Получаем все результаты
            output_text = ""
            for row in result:
                client_name = row[0]
                total_cost = row[1]
                output_text += f"Клиент: {client_name}, Общая стоимость услуг: {total_cost} рублей\n"

            self.output.setText(output_text)

            cursor.close()
            connection.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec_())
