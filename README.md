# UVM на допуск (Вариант №24)
## Описание проекта<br>
Проект реализует учебную виртуальную машину (УВМ) и инструменты для работы с ней:<br>
Ассемблер — преобразует программу с алгебраическим синтаксисом в бинарный формат УВМ<br>
Интерпретатор — исполняет бинарный код УВМ и формирует дамп памяти<br>
Кроссплатформенное GUI-приложение — позволяет писать, ассемблировать и запускать программы визуально<br>
Тестовые программы и дампы — примеры вычисления min() над векторами<br>
## Язык ассемблера УВМ
Ассемблер использует человекочитаемый алгебраический синтаксис<br>
Каждая инструкция помещается на одной строке:<br>
команда аргумент1 аргумент2 аргумент3<br>
## Поддерживаемые инструкции
1. Загрузка константы в память. load_const <br>
Формат: load_const B C<br>
Описание: сохранить число C в ячейку B.<br>
2. Чтение значения из памяти по адресу. read_value<br>
Формат: read_value B C<br>
Описание: memory[B] = memory[C]<br>
3. Запись значения в память по адресу, вычисляемому динамически. write_value 
Формат: write_value B C D<br>
Адрес вычисляется как: addr = memory[C] + D<br>
memory[addr] = memory[B]
4. Операция сравнения двух значений и запись минимума. min<br>
Формат: min B C D<br>
Описание: <br>
val1 = memory[D]<br>
val2 = memory[ memory[C] ]<br>
memory[B] = min(val1, val2)

| Команда     | Размер  | Описание                    |
| ----------- | ------- | --------------------------- |
| load_const  | 5 байт  | opcode + B + C (16 бит)     |
| read_value  | 5 байт  | opcode + B + C (16 бит)     |
| write_value | 4 байта | opcode + B + C + D (8+8+8)  |
| min         | 6 байт  | opcode + B + C + D (16 бит) |

## Структура проекта
uvm-project/<br>
│<br>
├── asm/                  # Исходные .asm программы<br>
├── bin/                  # Скомпилированные .bin файлы<br>
├── dumps/                # Дамп памяти после выполнения программ (.csv)<br>
│<br>
├── uvm_asm.py            # Ассемблер<br>
├── uvm_interp.py         # Интерпретатор<br>
├── uvm_gui.py            # GUI<br>
│<br>
├── README.md             # Документация 

# Запуск ассемблера
python uvm_asm.py -i asm/example1.asm -o bin/example1.bin -t 1<br>
Опция -t 1 выводит IR и байткод.
# Запуск интерпретатора
python uvm_interp.py -i bin/example1.bin -o dumps/example1.csv -r 0-100<br>
# Запуск GUI
python uvm_gui.py<br>
Позволяет:<br> 
✔ редактировать программу<br>
✔ ассемблировать<br>
✔ запускать интерпретатор<br>
✔ смотреть дамп памяти<br>
✔ копировать байткод<br>
Для того, чтобы увидеть байткод, необходимо полностью раскрыть окно gui<br>
## Этап 5: Решение тестовой задачи (min для векторов длины 8)
Программа vector_min.asm<br>
load_const 1 100<br>
load_const 2 40<br>
load_const 3 200<br>
load_const 4 201<br>
load_const 5 40<br>
load_const 6 0<br>
load_const 7 500<br>
load_const 8 700<br>

load_const 11 90<br>
load_const 12 200<br>
load_const 13 20<br>
load_const 14 220<br>
load_const 15 10000<br>
load_const 16 1<br>
load_const 17 700<br>
load_const 18 350<br>

min 1 1 11<br>
min 2 2 12<br>
min 3 3 13<br>
min 4 4 14<br>
min 5 5 15<br>
min 6 6 16<br>
min 7 7 17<br>
min 8 8 18<br>

Результат помещается в адреса 20–27.<br>
Дамп: vector_min.csv

Также еще две тестовые программы vector_min_test2.asm и vector_min_test3.asm<br>
Дамп: vector_min_test3.csv и vector_min_test2.csv













