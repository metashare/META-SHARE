#from out2_sup import *

import out2_sup as model_

rootObj = model_.rootTag(
    comments=[
        model_.comments(
            content_ = [
            model_.MixedContainer(1, 0, "", "1. This is a "),
            model_.MixedContainer(2, 2, "emp", "foolish"),
            model_.MixedContainer(1, 0, "", " comment.  It is "),
            model_.MixedContainer(2, 2, "emp", "really"),
            model_.MixedContainer(1, 0, "", " important."),
            ],
            valueOf_ = """1. This is a  comment.  It is  important.""",
        ),
        model_.comments(
            content_ = [
            model_.MixedContainer(1, 0, "", "2. This is a "),
            model_.MixedContainer(2, 2, "emp", "silly"),
            model_.MixedContainer(1, 0, "", " comment.  It is "),
            model_.MixedContainer(2, 2, "emp", "very"),
            model_.MixedContainer(1, 0, "", " significant."),
            ],
            valueOf_ = """2. This is a  comment.  It is  significant.""",
        ),
    ],
    person=[
        model_.person(
            ratio = 3.200000,
            id = 1,
            value = "abcd",
            name='Alberta',
            interest=[
                'gardening',
                'reading',
            ],
            category=5,
            agent=[
            ],
            promoter=[
            ],
        ),
        model_.person(
            id = 2,
            name='Bernardo',
            interest=[
                'programming',
            ],
            category=0,
            agent=[
                model_.agent(
                    firstname='Darren',
                    lastname='Diddly',
                    priority=4.500000,
                    info=model_.info(
                        rating = 5.330000,
                        type_ = 321,
                        name = "Albert Abasinian",
                    ),
                ),
            ],
            promoter=[
            ],
        ),
        model_.person(
            id = 3,
            name='Charlie',
            interest=[
                'people',
                'cats',
                'dogs',
            ],
            category=8,
            agent=[
            ],
            promoter=[
                model_.booster(
                    firstname='David',
                    lastname='Donaldson',
                    other_value=[
                    ],
                    type_=[
                    ],
                    client_handler=[
                    ],
                ),
                model_.booster(
                    firstname='Edward',
                    lastname='Eddleberry',
                    other_value=[
                    ],
                    type_=[
                    ],
                    client_handler=[
                    ],
                ),
            ],
        ),
        model_.person(
            id = 4,
        ),
    ],
    programmer=[
        model_.programmer(
            language = "python",
            area = "xml",
            id = 2,
            name='Charles Carlson',
            interest=[
                'programming',
            ],
            category=2233,
            agent=[
                model_.agent(
                    firstname='Ernest',
                    lastname='Echo',
                    priority=3.800000,
                    info=model_.info(
                        rating = 5.330000,
                        type_ = 321,
                        name = "George Gregory",
                    ),
                ),
            ],
            promoter=[
            ],
            description='A very happy programmer',
            email='charles@happyprogrammers.com',
            elposint=14,
            elnonposint=0,
            elnegint=-12,
            elnonnegint=4,
            eldate='2005-04-26',
            eltoken='aa bb cc dd',
            elshort=123,
            ellong=13241234123412341234,
            elparam=model_.param(
                semantic = "a big semantic",
                name = "Davy",
                id = "id001",
                valueOf_ = """""",
            ),
        ),
    ],
    python_programmer=[
        model_.python_programmer(
            nick_name = "davy",
            language = "python",
            area = "xml",
            vegetable = "tomato",
            fruit = "peach",
            ratio = 8.700000,
            id = 232,
            value = "abcd",
            name='Darrel Dawson',
            interest=[
                'hang gliding',
            ],
            category=3344,
            agent=[
                model_.agent(
                    firstname='Harvey',
                    lastname='Hippolite',
                    priority=5.200000,
                    info=model_.info(
                        rating = 6.550000,
                        type_ = 543,
                        name = "Harvey Hippolite",
                    ),
                ),
            ],
            promoter=[
            ],
            description='An object-orientated programmer',
            email='darrel@happyprogrammers.com',
            favorite_editor='jed',
        ),
    ],
    java_programmer=[
        model_.java_programmer(
            nick_name = "davy",
            language = "python",
            area = "xml",
            vegetable = "tomato",
            fruit = "peach",
            ratio = 8.700000,
            id = 232,
            value = "abcd",
            name='Darrel Dawson',
            interest=[
                'hang gliding',
            ],
            category=3344,
            agent=[
                model_.agent(
                    firstname='Harvey',
                    lastname='Hippolite',
                    priority=5.200000,
                    info=model_.info(
                        rating = 6.550000,
                        type_ = 543,
                        name = "Harvey Hippolite",
                    ),
                ),
            ],
            promoter=[
            ],
            description='An object-orientated programmer',
            email='darrel@happyprogrammers.com',
            favorite_editor='jed',
        ),
    ],
)
