#
# Call Schedule v0.1
# Author: Aseem Sood
#

import csv
from datetime import datetime, timedelta
from enum import Enum

# Constants

MAX_SLOTS = 100  # large number to be overridden if needed
INITIAL_LAST_DATE_ASSIGNED = datetime(2020, 1, 1)
SLOT_TYPE_WEEKEND = 'weekend'
SLOT_TYPE_WEEKDAY = 'weekday'
SLOT_SUBTYPE = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    6: "sunday"
}

##########
# Helpers#
##########


def date_range_to_list(start_date, end_date):
    date_list = []
    day_count = (end_date - start_date).days + 1
    for single_date in (start_date + timedelta(days=n) for n in range(day_count)):
        date_list.append(single_date)
    return date_list


##########
# Classes#
##########


class Slot():
    def __init__(self, type, start_date, end_date):
        self.type = type  # weekday, weekend, skipped, etc
        self.start_date = start_date
        self.end_date = end_date
        self.assigned_to = None

        # calculate subtype
        # if self.type == SLOT_TYPE_WEEKEND:
        #     self.subtype = SLOT_TYPE_WEEKEND
        if self.type == SLOT_TYPE_WEEKDAY:
            self.subtype = SLOT_SUBTYPE[self.start_date.weekday()]
        else:
            self.subtype = None

    def __str__(self):
        if self.type == SLOT_TYPE_WEEKDAY:
            return 'Weekday: {0} assigned to {1}'.format(self.start_date.strftime('%m/%d/%Y'), self.assigned_to.name)
        else:
            return 'Weekend: {0} - {1} assigned to {2}'.format(self.start_date.strftime('%m/%d/%Y'), self.end_date.strftime('%m/%d/%Y'), self.assigned_to.name)

    @staticmethod
    def generate_stats(slots):
        names = {}
        for slot in slots:
            name = slot.assigned_to.name
            if name not in names:
                names[name] = {
                    SLOT_TYPE_WEEKDAY: 0,
                    SLOT_TYPE_WEEKEND: 0,
                    SLOT_SUBTYPE[0]: 0,
                    SLOT_SUBTYPE[1]: 0,
                    SLOT_SUBTYPE[2]: 0,
                    SLOT_SUBTYPE[3]: 0,
                    SLOT_SUBTYPE[6]: 0
                }
            entry = names[name]

            entry[slot.type] += 1

            if slot.subtype != None:
                entry[slot.subtype] += 1

        for name in names.keys():
            print('{0}'.format(name))
            entry = names[name]
            print('\tWeekends: {0}, Weekdays: {1}'.format(
                entry[SLOT_TYPE_WEEKEND], entry[SLOT_TYPE_WEEKDAY]))
            print('\t\tMon: {0}, Tue: {1}, Wed: {2}, Thu: {3}, Sun: {4}'.format(
                entry[SLOT_SUBTYPE[0]], entry[SLOT_SUBTYPE[1]], entry[SLOT_SUBTYPE[2]], entry[SLOT_SUBTYPE[3]], entry[SLOT_SUBTYPE[6]]))
            # , Mon: {2}, Tue: {3}, Wed: {4}, Thursdays: {5}, Sundays: {6}'.format())


class Person:
    def __init__(self, name):
        self.name = name  # string
        self.blocked_dates = set()  # list
        self.max_slots = {
            # large initial value to be overwritten by real data later
            SLOT_TYPE_WEEKEND: MAX_SLOTS,
            SLOT_TYPE_WEEKDAY: MAX_SLOTS  # Not currently used; here to reduce duplicate logic
        }
        self.stats = {
            SLOT_TYPE_WEEKDAY: 0,
            SLOT_TYPE_WEEKEND: 0
        }
        self.last_date_assigned = INITIAL_LAST_DATE_ASSIGNED

    def is_available(self, proposed_dates):
        # todo: can improve algorithm
        for date in proposed_dates:
            if date in self.blocked_dates:
                return False
        return True

    def add_blocked_dates(self, start_date, end_date):
        if not end_date:
            end_date = start_date
        self.blocked_dates.update(date_range_to_list(start_date, end_date))

    def assign_slot(self, slot):
        slot_type = slot.type
        # update stats
        self.stats[slot_type] += 1
        # update last_assigned_date
        self.last_date_assigned = slot.end_date

    def __str__(self):
        max_weekends = self.max_slots[SLOT_TYPE_WEEKEND]
        if max_weekends == MAX_SLOTS:
            max_weekends = '-'
        return '{0: <20} | Day blocked off: {1: <2}, Assigned: {2} weekends, {3} weekdays | Max weekends: {4}'.format(
            self.name, len(self.blocked_dates), self.stats[SLOT_TYPE_WEEKEND], self.stats[SLOT_TYPE_WEEKDAY], max_weekends)

    @staticmethod
    def sort_by_least_busy_person(persons_list, slot_to_be_filled):
        slot_type = slot_to_be_filled.type

        # remove anyone who has hit their max weekends
        available = filter(lambda person: person.max_slots[slot_type] >
                           person.stats[slot_type], persons_list)
        # remove anyone who has this date blocked
        available = filter(lambda person: person.is_available(date_range_to_list(
            slot_to_be_filled.start_date, slot_to_be_filled.end_date)), available)
        # return sorted list by count and then last picked

        return sorted(available, key=lambda person: (person.stats[slot_type], person.last_date_assigned))


##################


def read_csv(filename):
    print("\nReading file: ", filename)

    persons_list = []
    skipped_slots_list = set()
    with open(filename) as csvfile:
        file_reader = csv.reader(csvfile, delimiter=',')
        for index, row in enumerate(file_reader):
            if (index == 0 or row[0] == ''):
                # header row, skip
                continue

            # parse row
            name = row[0]
            type_row = row[1]
            if (len(row[2]) > 0):
                start_date = datetime.strptime(row[2], '%m/%d/%Y')
            if (len(row[3]) > 0):
                end_date = datetime.strptime(row[3], '%m/%d/%Y')
                # check for data integrity
                if (end_date - start_date).days < 0:
                    raise Exception("Invalid data: ", row)

            # Logic based on type
            # Try to find the name in persons_list
            index = next((i for i, person in enumerate(
                persons_list) if name == person.name), None)

            # if name not found
            if index == None:
                person = Person(name)
                persons_list.append(person)
            else:
                person = persons_list[index]

            if type_row == 'vacation':
                person.add_blocked_dates(start_date, end_date)
            if type_row == 'holiday':
                date_range = date_range_to_list(start_date, end_date)
                skipped_slots_list.update(date_range)
            if type_row == 'max_weekends':
                person.max_slots[SLOT_TYPE_WEEKEND] = int(row[4])

    print('Skipped days: {0}'.format(len(skipped_slots_list)))

    print("\n")
    return persons_list, skipped_slots_list


def create_slots(start_date, end_date, skipped_slots):
    print("Generating slots...\n")
    # Create a slot for each day, weekend, etc
    day_count = (end_date - start_date).days + 1
    print("Days in range: ", day_count)
    slot_list = []
    for single_date in (start_date + timedelta(days=n) for n in range(day_count)):
        weekday = single_date.weekday()
        if single_date in skipped_slots:
            print("Skipping ", single_date.strftime('%m/%d/%Y'))
            continue
        if (weekday < 4 or weekday == 6):  # Mon - Thu, Sun
            slot = Slot(SLOT_TYPE_WEEKDAY, single_date, single_date)
            slot_list.append(slot)
        elif (single_date.weekday() == 4):  # Fri
            slot = Slot(SLOT_TYPE_WEEKEND, single_date,
                        single_date+timedelta(days=2))
            slot_list.append(slot)
        # skip saturday

    print("\nweekday slots: ", len(list(filter(
        lambda slot: slot.type == SLOT_TYPE_WEEKDAY, slot_list))))
    print("weekend slots: ", len(list(filter(
        lambda slot: slot.type == SLOT_TYPE_WEEKEND, slot_list))))
    print("skipped slots: ", len(skipped_slots))

    print("\n")
    return slot_list


def create_schedule(persons_list, slot_list):
    # start filling slots

    for slot in slot_list:
        priority_person_list = Person.sort_by_least_busy_person(
            persons_list, slot)
        if len(priority_person_list) == 0:
            print("Error")
            raise Exception("No one found for ", slot)

        # Schedule slot
        slot.assigned_to = priority_person_list[0]

        # update stats
        priority_person_list[0].assign_slot(slot)


def print_schedule(slots):
    for slot in slots:
        print(slot)


if __name__ == "__main__":

    print('Call Scheduler Started...')
    # read csv data
    persons_list, skipped_slots_list = read_csv(
        'sample_dates - sample_schedule.csv')

    print("Input data summary: ")
    for person in persons_list:
        print('\t', person)

    print()

    # generate slots
    # TODO: allow input from csv also
    start_date = datetime(2020, 7, 1)
    end_date = datetime(2021, 1, 3)
    slots = create_slots(start_date, end_date, skipped_slots_list)

    # create schedule
    create_schedule(persons_list, slots)

    print_schedule(slots)

    print("\nStats across everyone: ")
    Slot.generate_stats(slots)

    print('\n...Finished!')
    pass
