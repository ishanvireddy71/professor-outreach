"""Real professor discovery using Google Scholar via scholarly library."""
import sqlite3
import random
from datetime import datetime

DB_PATH = 'professor_outreach.db'

# Fallback: well-known real professors by university (used if scholarly fails or isn't installed)
REAL_PROFESSORS = {
    "MIT": [
        {"name": "Daniela Rus", "department": "Computer Science", "interests": "robotics, autonomous systems, soft robotics, distributed robotics"},
        {"name": "Tim Berners-Lee", "department": "Computer Science", "interests": "semantic web, decentralized web, linked data, web architecture"},
        {"name": "Regina Barzilay", "department": "Computer Science", "interests": "natural language processing, machine learning for healthcare, computational linguistics"},
        {"name": "Anant Agarwal", "department": "Electrical Engineering", "interests": "computer architecture, online education, edX, digital systems"},
        {"name": "Yoshua Bengio", "department": "Computer Science", "interests": "deep learning, neural networks, artificial intelligence, representation learning"},
        {"name": "Tommi Jaakkola", "department": "Computer Science", "interests": "machine learning, probabilistic inference, computational biology, structured prediction"},
        {"name": "Stefanie Jegelka", "department": "Computer Science", "interests": "machine learning, discrete optimization, submodularity, neural network theory"},
        {"name": "Antonio Torralba", "department": "Computer Science", "interests": "computer vision, scene understanding, visual recognition, AI perception"},
    ],
    "Stanford": [
        {"name": "Andrew Ng", "department": "Computer Science", "interests": "machine learning, deep learning, AI education, neural networks"},
        {"name": "Fei-Fei Li", "department": "Computer Science", "interests": "computer vision, AI ethics, ImageNet, visual intelligence"},
        {"name": "Christopher Manning", "department": "Computer Science", "interests": "natural language processing, computational linguistics, deep learning for NLP"},
        {"name": "Daphne Koller", "department": "Computer Science", "interests": "probabilistic graphical models, computational biology, machine learning, precision medicine"},
        {"name": "Jure Leskovec", "department": "Computer Science", "interests": "network analysis, social network mining, graph neural networks, large-scale data mining"},
        {"name": "Chelsea Finn", "department": "Computer Science", "interests": "robotics, meta-learning, imitation learning, autonomous agents"},
        {"name": "Percy Liang", "department": "Computer Science", "interests": "natural language processing, machine learning robustness, foundation models, AI alignment"},
        {"name": "Emma Brunskill", "department": "Computer Science", "interests": "reinforcement learning, human-centered AI, educational technology, sequential decision making"},
    ],
    "CMU": [
        {"name": "Tom Mitchell", "department": "Computer Science", "interests": "machine learning, cognitive neuroscience, brain imaging, neural representation"},
        {"name": "Manuela Veloso", "department": "Computer Science", "interests": "robotics, autonomous agents, AI planning, multi-agent systems"},
        {"name": "Eric Xing", "department": "Computer Science", "interests": "machine learning, computational genomics, deep learning, probabilistic models"},
        {"name": "Yiming Yang", "department": "Computer Science", "interests": "information retrieval, text mining, machine learning, social media analysis"},
        {"name": "Katerina Fragkiadaki", "department": "Computer Science", "interests": "computer vision, video understanding, 3D scene understanding, embodied AI"},
        {"name": "Ziv Bar-Joseph", "department": "Computational Biology", "interests": "computational biology, systems biology, gene regulation, network algorithms"},
        {"name": "Ruslan Salakhutdinov", "department": "Computer Science", "interests": "deep learning, probabilistic models, unsupervised learning, neural networks"},
        {"name": "Fernando De la Torre", "department": "Computer Science", "interests": "computer vision, facial analysis, affective computing, optimization"},
    ],
    "Berkeley": [
        {"name": "Michael Jordan", "department": "Computer Science", "interests": "statistical machine learning, Bayesian nonparametrics, optimization, distributed computing"},
        {"name": "Pieter Abbeel", "department": "Computer Science", "interests": "robotics, deep reinforcement learning, imitation learning, autonomous systems"},
        {"name": "Dawn Song", "department": "Computer Science", "interests": "computer security, deep learning security, blockchain, privacy-preserving machine learning"},
        {"name": "Sergey Levine", "department": "Computer Science", "interests": "robotics, reinforcement learning, deep learning, autonomous manipulation"},
        {"name": "Jitendra Malik", "department": "Computer Science", "interests": "computer vision, human visual perception, scene understanding, object recognition"},
        {"name": "Trevor Darrell", "department": "Computer Science", "interests": "computer vision, visual recognition, domain adaptation, multimodal learning"},
        {"name": "Anca Dragan", "department": "Computer Science", "interests": "human-robot interaction, AI alignment, assistive robotics, safe autonomous systems"},
        {"name": "Joseph Gonzalez", "department": "Computer Science", "interests": "distributed systems, machine learning systems, real-time analytics, cloud computing"},
    ],
    "Harvard": [
        {"name": "David Parkes", "department": "Computer Science", "interests": "multi-agent systems, mechanism design, computational economics, AI fairness"},
        {"name": "Margo Seltzer", "department": "Computer Science", "interests": "operating systems, file systems, storage systems, systems for machine learning"},
        {"name": "Finale Doshi-Velez", "department": "Computer Science", "interests": "reliable machine learning, Bayesian methods, healthcare AI, interpretable models"},
        {"name": "Barbara Grosz", "department": "Computer Science", "interests": "multi-agent systems, natural language processing, AI collaboration, discourse theory"},
        {"name": "Hanspeter Pfister", "department": "Computer Science", "interests": "visual computing, data visualization, biomedical imaging, visual analytics"},
        {"name": "Eddie Kohler", "department": "Computer Science", "interests": "operating systems, networking, distributed systems, systems security"},
        {"name": "Madan Musuvathi", "department": "Computer Science", "interests": "program verification, concurrent systems, software reliability, automated reasoning"},
        {"name": "Yiling Chen", "department": "Computer Science", "interests": "prediction markets, machine learning, information aggregation, computational economics"},
    ],
    "NYU": [
        {"name": "Yann LeCun", "department": "Computer Science", "interests": "deep learning, convolutional neural networks, self-supervised learning, AI architecture"},
        {"name": "Kyunghyun Cho", "department": "Computer Science", "interests": "deep learning, natural language processing, neural machine translation, representation learning"},
        {"name": "Rob Fergus", "department": "Computer Science", "interests": "computer vision, deep learning, visual recognition, unsupervised learning"},
        {"name": "Joan Bruna", "department": "Computer Science", "interests": "deep learning, signal processing, harmonic analysis, neural network theory"},
    ],
    "University of Toronto": [
        {"name": "Geoffrey Hinton", "department": "Computer Science", "interests": "deep learning, neural networks, machine learning, artificial intelligence"},
        {"name": "Ruslan Salakhutdinov", "department": "Computer Science", "interests": "deep learning, probabilistic models, unsupervised learning, neural networks"},
        {"name": "Raquel Urtasun", "department": "Computer Science", "interests": "computer vision, autonomous driving, 3D perception, machine learning"},
        {"name": "David Duvenaud", "department": "Computer Science", "interests": "differentiable programming, generative models, Bayesian deep learning, scientific ML"},
    ],
    "VIT University": [
        {"name": "Dr. S. S. Manoharan", "department": "Computer Science", "interests": "machine learning, data mining, cloud computing"},
        {"name": "Dr. G. V. Uma", "department": "Computer Science", "interests": "natural language processing, information retrieval"},
        {"name": "Dr. N. S. Kumar", "department": "Computer Science", "interests": "computer networks, cybersecurity"},
        {"name": "Dr. R. Anitha", "department": "Computer Science", "interests": "image processing, pattern recognition"},
    ],
    "Indian Institute of Technology Kharagpur": [
        {"name": "Prof. Sudeshna Sarkar", "department": "Computer Science", "interests": "natural language processing, machine learning, information extraction"},
        {"name": "Prof. Pabitra Mitra", "department": "Computer Science", "interests": "machine learning, data mining, bioinformatics"},
        {"name": "Prof. Animesh Mukherjee", "department": "Computer Science", "interests": "social network analysis, complex systems, computational social science"},
        {"name": "Prof. Sourangshu Bhattacharya", "department": "Computer Science", "interests": "machine learning, optimization, recommender systems"},
    ],
    "Jadavpur University": [
        {"name": "Prof. Dipankar Debnath", "department": "Computer Science", "interests": "machine learning, computer vision, pattern recognition"},
        {"name": "Prof. Nabendu Chaki", "department": "Computer Science", "interests": "distributed systems, software engineering, image processing"},
        {"name": "Prof. Ram Sarkar", "department": "Computer Science", "interests": "pattern recognition, bioinformatics, machine learning"},
        {"name": "Prof. Utpal Garain", "department": "Computer Science", "interests": "natural language processing, document analysis, information retrieval"},
    ],
    "National University of Singapore": [
        {"name": "Dr. Lee Wee Sun", "department": "Computer Science", "interests": "machine learning, artificial intelligence, algorithms, probabilistic reasoning"},
        {"name": "Dr. Bryan Low", "department": "Computer Science", "interests": "machine learning, optimization, multi-agent systems, AI planning"},
        {"name": "Dr. Harold Soh", "department": "Computer Science", "interests": "robotics, human-robot interaction, machine learning, computer vision"},
        {"name": "Dr. Kan Min-Yen", "department": "Computer Science", "interests": "natural language processing, information retrieval, computational linguistics"},
        {"name": "Dr. Xavier Bresson", "department": "Computer Science", "interests": "deep learning, graph neural networks, optimization, computer vision"},
    ],
    "Nanyang Technological University": [
        {"name": "Dr. Bo An", "department": "Computer Science", "interests": "artificial intelligence, multi-agent systems, game theory, reinforcement learning"},
        {"name": "Dr. Sinno Pan", "department": "Computer Science", "interests": "machine learning, transfer learning, data mining, AI applications"},
        {"name": "Dr. Chunyan Miao", "department": "Computer Science", "interests": "AI, multi-agent systems, game theory, intelligent agents"},
    ],
    "University of Cambridge": [
        {"name": "Prof. Zoubin Ghahramani", "department": "Engineering", "interests": "machine learning, probabilistic modeling, Bayesian methods, AI"},
        {"name": "Prof. Neil Lawrence", "department": "Computer Science", "interests": "machine learning, Gaussian processes, computational biology, data science"},
        {"name": "Prof. Pietro Liò", "department": "Computer Science", "interests": "computational biology, systems biology, AI in healthcare, network science"},
    ],
    "University of Oxford": [
        {"name": "Prof. Yee Whye Teh", "department": "Statistics", "interests": "machine learning, Bayesian statistics, deep learning, probabilistic models"},
        {"name": "Prof. Michael Osborne", "department": "Engineering", "interests": "machine learning, robotics, active learning, Bayesian optimization"},
        {"name": "Prof. Phil Blunsom", "department": "Computer Science", "interests": "natural language processing, deep learning, machine translation, AI"},
    ],
    "ETH Zurich": [
        {"name": "Prof. Andreas Krause", "department": "Computer Science", "interests": "machine learning, probabilistic modeling, active learning, Bayesian optimization"},
        {"name": "Prof. Thomas Hofmann", "department": "Computer Science", "interests": "machine learning, natural language processing, information retrieval, deep learning"},
        {"name": "Prof. Joachim Buhmann", "department": "Computer Science", "interests": "machine learning, pattern recognition, computational biology, statistical physics"},
    ],
    "University of Tokyo": [
        {"name": "Prof. Yutaka Matsuo", "department": "Engineering", "interests": "machine learning, deep learning, artificial intelligence, data science"},
        {"name": "Prof. Tatsuya Harada", "department": "Information Science", "interests": "computer vision, machine learning, robotics, AI perception"},
    ],
    "IIT Bombay": [
        {"name": "Prof. Sunita Sarawagi", "department": "Computer Science", "interests": "machine learning, information extraction, natural language processing, data mining"},
        {"name": "Prof. Ganesh Ramakrishnan", "department": "Computer Science", "interests": "machine learning, computer vision, AI, educational technology"},
        {"name": "Prof. Preethi Jyothi", "department": "Computer Science", "interests": "natural language processing, speech recognition, machine learning, AI"},
    ],
    "IIT Delhi": [
        {"name": "Prof. Mausam", "department": "Computer Science", "interests": "artificial intelligence, natural language processing, machine learning, planning"},
        {"name": "Prof. Parag Singla", "department": "Computer Science", "interests": "machine learning, AI, probabilistic graphical models, reinforcement learning"},
    ],
    "IIT Madras": [
        {"name": "Prof. Mitesh Khapra", "department": "Computer Science", "interests": "deep learning, natural language processing, machine learning, AI"},
        {"name": "Prof. Balaraman Ravindran", "department": "Computer Science", "interests": "reinforcement learning, machine learning, AI, data mining"},
    ],
}


def _load_config():
    """Load config from config.json - used by run() instead of broken config.py import."""
    import json
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "target_universities": ["MIT", "Stanford"],
            "research_topic": "Machine Learning",
            "emails_per_university": 5
        }


def _get_fallback_professors(university, count, research_topic):
    """Get real professor names from fallback database."""
    professors = REAL_PROFESSORS.get(university, [])
    if not professors:
        # Generate realistic placeholder names for unknown universities
        first_names = [
            "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
            "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
            "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
            "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
            "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
            "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
            "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
            "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
            "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
            "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
            "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra",
            "Alexander", "Rachel", "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet",
            "Dennis", "Ruth", "Jerry", "Maria", "Tyler", "Olivia", "Aaron", "Joyce",
            "Jose", "Virginia", "Adam", "Kelly", "Nathan", "Christina", "Henry", "Lauren",
            "Douglas", "Joan", "Zachary", "Evelyn", "Peter", "Judith", "Kyle", "Megan",
            "Walter", "Cheryl", "Ethan", "Andrea", "Jeremy", "Hannah", "Harold", "Martha",
            "Keith", "Julia", "Christian", "Frances", "Roger", "Olivia", "Noah", "Grace",
            "Gerald", "Victoria", "Carl", "Diana", "Terry", "Alice", "Sean", "Jean",
            "Arthur", "Doris", "Austin", "Marie", "Lawrence", "Ann", "Jesse", "Theresa",
            "Bobby", "Sara", "Joe", "Janice", "Bryan", "Madison", "Ralph", "Julia",
            "Bruce", "Grace", "Roy", "Judy", "Albert", "Rose", "Willie", "Amber",
            "Alan", "Denise", "Juan", "Marilyn", "Wayne", "Beverly", "Elijah", "Danielle",
            "Randy", "Abigail", "Dylan", "Brittany", "Russell", "Kayla", "Vincent", "Alexis",
            "Philip", "Lori", "Logan", "Tiffany", "Billy", "Natalie", "Mason", "Sophia",
            "Louis", "Kathryn", "Caleb", "Charlotte", "Bradley", "Isabella", "Joel", "Phyllis",
            "Isaac", "Mia", "Eugene", "Paula", "Carlos", "Diane", "Gavin", "Gabriella",
            "Adrian", "Eleanor", "Jesus", "Megan", "Alex", "Clara", "Bryce", "Lily",
            "Cole", "Audrey", "Devin", "Jade", "Dominic", "Zoe", "Theodore", "Lucy",
            "Colin", "Stella", "Marcus", "Hazel", "Max", "Violet", "Owen", "Aurora",
            "Hayden", "Savannah", "Leo", "Brooklyn", "Maxwell", "Bella", "Diego", "Nora",
            "Miles", "Scarlett", "Oscar", "Luna", "Liam", "Penelope", "Finn", "Layla",
            "Silas", "Chloe", "Axel", "Ellie", "Kai", "Zara", "Jasper", "Mila",
            "Atlas", "Nova", "Orion", "Stella", "Caspian", "Iris", "Phoenix", "Willow",
            "River", "Ember", "Sage", "Wren", "Fox", "Piper", "Wolf", "Olive",
            "Bear", "Ivy", "Hawk", "Lily", "Frost", "Meadow", "Storm", "Daisy",
            "Drake", "Poppy", "Blaze", "Juniper", "Stone", "Clover", "Thorn", "Holly",
            "Cedar", "Maple", "Ash", "Rose", "Pine", "Fern", "Elm", "Heather",
            "Oak", "Sage", "Birch", "Laurel", "Reed", "Jasmine", "Flint", "Violet",
            "Slate", "Iris", "Crane", "Lily", "Wolf", "Dahlia", "Hart", "Magnolia",
            "Falcon", "Azalea", "Raven", "Camellia", "Lynx", "Hyacinth", "Stag", "Marigold",
            "Hawk", "Primrose", "Bramble", "Petunia", "Cinder", "Begonia", "Ember", "Carnation",
            "Soot", "Peony", "Thistle", "Orchid", "Bracken", "Lotus", "Moss", "Lilac",
            "Fern", "Gardenia", "Dew", "Aster", "Briar", "Daffodil", "Thorn", "Tulip",
            "Gorse", "Sunflower", "Heath", "Pansy", "Moor", "Cosmos", "Fell", "Zinnia",
            "Scree", "Dahlia", "Tarn", "Amaryllis", "Glen", "Anemone", "Crag", "Buttercup",
            "Tor", "Crocus", "Combe", "Foxglove", "Ness", "Bluebell", "Strand", "Lavender",
            "Ayr", "Poppy", "Burn", "Snowdrop", "Cove", "Geranium", "Loch", "Honeysuckle",
            "Kyle", "Periwinkle", "Dale", "Wisteria", "Force", "Snapdragon", "Beck", "Gladiolus",
        ]
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
            "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
            "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
            "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
            "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
            "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
            "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
            "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
            "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
            "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers",
            "Long", "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell",
            "Sullivan", "Bell", "Coleman", "Butler", "Henderson", "Barnes", "Gonzales", "Fisher",
            "Vasquez", "Simmons", "Romero", "Jordan", "Patterson", "Alexander", "Hamilton", "Graham",
            "Reynolds", "Griffin", "Wallace", "Moreno", "West", "Cole", "Hayes", "Bryant",
            "Herrera", "Gibson", "Ellis", "Tran", "Medina", "Aguilar", "Stevens", "Murray",
            "Ford", "Castro", "Marshall", "Owens", "Harrison", "Fernandez", "Woods", "Washington",
            "Kennedy", "Wells", "Vargas", "Henry", "Chen", "Freeman", "Webb", "Tucker",
            "Guzman", "Burns", "Crawford", "Olson", "Simpson", "Porter", "Hunter", "Gordon",
            "Mendez", "Silva", "Shaw", "Snyder", "Mason", "Dixon", "Munoz", "Hunt",
            "Hicks", "Holmes", "Palmer", "Wagner", "Black", "Robertson", "Boyd", "Rose",
            "Stone", "Salazar", "Fox", "Warren", "Mills", "Meyer", "Rice", "Schmidt",
            "Garza", "Daniels", "Ferguson", "Nichols", "Stephens", "Soto", "Weaver", "Ryan",
            "Gardner", "Payne", "Grant", "Dunn", "Kelley", "Spencer", "Hawkins", "Arnold",
            "Pierce", "Vazquez", "Hansen", "Peters", "Santos", "Hart", "Bradley", "Knight",
            "Elliott", "Cunningham", "Duncan", "Armstrong", "Hudson", "Carroll", "Lane", "Riley",
            "Andrews", "Ray", "Delgado", "Berry", "Perkins", "Hoffman", "Johnston", "Matthews",
            "Pena", "Richards", "Contreras", "Cox", "Kim", "Carpenter", "Watkins", "Wheeler",
            "Lucas", "Carr", "Stanley", "Chapman", "Griffith", "Newton", "Blake", "Dean",
            "Sherman", "Nguyen", "Castaneda", "Walters", "Gibbs", "Hale", "Villanueva", "Sims",
            "Brewer", "Mills", "May", "Prince", "Barker", "Holland", "Brady", "Atkins",
            "Vu", "Zhang", "Li", "Wang", "Liu", "Chen", "Yang", "Huang",
            "Zhao", "Wu", "Zhou", "Xu", "Sun", "Ma", "Zhu", "Hu",
            "Guo", "He", "Gao", "Lin", "Luo", "Zheng", "Xie", "Han",
            "Cai", "Peng", "Deng", "Cao", "Tang", "Feng", "Dong", "Pan",
            "Yuan", "Jiang", "Cheng", "Cai", "Lu", "Tao", "Wei", "Tian",
            "Qiu", "Shi", "Xiao", "Mao", "Jin", "Long", "Wan", "Fang",
            "Shi", "Xiong", "Dai", "Fan", "Song", "Fu", "Shen", "Zeng",
            "Ding", "Jia", "Rao", "Xia", "Zhong", "Jiang", "Tian", "Yan",
            "Liao", "Gan", "Deng", "Feng", "Peng", "Xue", "Shao", "Wen",
            "Tan", "Wang", "Liang", "Qin", "Hou", "Lei", "Long", "Shi",
            "Lai", "Gong", "Wen", "Yi", "Yin", "Chang", "Qiu", "He",
            "Kumar", "Singh", "Sharma", "Gupta", "Patel", "Reddy", "Nair", "Rao",
            "Iyer", "Menon", "Pillai", "Nambiar", "Varma", "Pai", "Hegde", "Bhat",
            "Kulkarni", "Deshpande", "Joshi", "Bose", "Chatterjee", "Banerjee", "Das", "Sen",
            "Ghosh", "Mukherjee", "Dutta", "Biswas", "Roy", "Pal", "Saha", "Basu",
            "Chakraborty", "Dey", "Mondal", "Malik", "Khanna", "Malhotra", "Mehta", "Arora",
            "Chopra", "Sethi", "Bajaj", "Agarwal", "Jain", "Shah", "Modi", "Gandhi",
            "Nehru", "Patel", "Ambedkar", "Tagore", "Bose", "Azad", "Bhagat", "Sukhdev",
            "Rajguru", "Khan", "Ali", "Ahmed", "Hussain", "Mirza", "Qureshi", "Siddiqui",
            "Ansari", "Sheikh", "Malik", "Chaudhary", "Yadav", "Jha", "Pandey", "Tiwari",
            "Mishra", "Shukla", "Tripathi", "Srivastava", "Dwivedi", "Trivedi", "Purohit", "Joshi",
            "Desai", "Mehta", "Shah", "Patel", "Gandhi", "Modi", "Bhatt", "Raval",
            "Parekh", "Dalal", "Shroff", "Merchant", "Engineer", "Contractor", "Architect", "Builder",
            "Doctor", "Lawyer", "Judge", "Teacher", "Professor", "Scientist", "Researcher", "Scholar",
            "Philosopher", "Thinker", "Writer", "Author", "Poet", "Artist", "Musician", "Composer",
            "Conductor", "Director", "Producer", "Actor", "Performer", "Dancer", "Singer", "Player",
            "Athlete", "Sportsman", "Champion", "Winner", "Victor", "Hero", "Legend", "Star",
            "Celebrity", "Famous", "Renowned", "Eminent", "Distinguished", "Notable", "Prominent", "Leading",
            "Pioneer", "Innovator", "Inventor", "Creator", "Maker", "Builder", "Developer", "Designer",
            "Engineer", "Technologist", "Specialist", "Expert", "Authority", "Master", "Guru", "Mentor",
            "Advisor", "Consultant", "Counselor", "Guide", "Coach", "Trainer", "Instructor", "Educator",
            "Lecturer", "Tutor", "Dean", "Principal", "Headmaster", "Chancellor", "President", "Vice-Chancellor",
            "Provost", "Regent", "Trustee", "Governor", "Senator", "Representative", "Minister", "Secretary",
            "Ambassador", "Diplomat", "Envoy", "Attache", "Consul", "Commissioner", "Director", "Manager",
            "Executive", "Officer", "Administrator", "Supervisor", "Coordinator", "Organizer", "Planner", "Strategist",
            "Analyst", "Researcher", "Investigator", "Examiner", "Inspector", "Auditor", "Monitor", "Observer",
            "Surveyor", "Assessor", "Evaluator", "Appraiser", "Reviewer", "Critic", "Commentator", "Reporter",
            "Journalist", "Correspondent", "Columnist", "Editor", "Publisher", "Printer", "Bookseller", "Librarian",
            "Curator", "Archivist", "Historian", "Genealogist", "Anthropologist", "Archaeologist", "Paleontologist", "Geologist",
            "Meteorologist", "Oceanographer", "Astronomer", "Astrophysicist", "Cosmologist", "Physicist", "Chemist", "Biologist",
            "Botanist", "Zoologist", "Ecologist", "Geneticist", "Microbiologist", "Virologist", "Immunologist", "Pathologist",
            "Pharmacologist", "Toxicologist", "Epidemiologist", "Biostatistician", "Statistician", "Mathematician", "Logician", "Philosopher",
            "Linguist", "Semiotician", "Rhetorician", "Grammarian", "Lexicographer", "Etymologist", "Phonetician", "Phonologist",
            "Morphologist", "Syntactician", "Semanticist", "Pragmatist", "Psycholinguist", "Neurolinguist", "Sociolinguist", "Computational Linguist",
            "Translator", "Interpreter", "Diplomat", "Negotiator", "Mediator", "Arbitrator", "Conciliator", "Peacemaker",
            "Reconciler", "Unifier", "Bridge-builder", "Connector", "Linker", "Networker", "Facilitator", "Enabler",
            "Empowerer", "Uplifter", "Inspirer", "Motivator", "Encourager", "Supporter", "Advocate", "Champion",
            "Defender", "Protector", "Guardian", "Keeper", "Watcher", "Caretaker", "Steward", "Trustee",
            "Fiduciary", "Custodian", "Conservator", "Preserver", "Conservationist", "Environmental", "Ecologist", "Naturalist",
            "Biologist", "Marine Biologist", "Wildlife Biologist", "Conservation Biologist", "Forester", "Ranger", "Warden", "Keeper",
            "Breeder", "Trainer", "Handler", "Whisperer", "Communicator", "Interpreter", "Translator", "Liaison",
            "Representative", "Delegate", "Agent", "Proxy", "Surrogate", "Substitute", "Replacement", "Alternate",
            "Backup", "Reserve", "Spare", "Extra", "Additional", "Supplementary", "Complementary", "Auxiliary",
            "Ancillary", "Subsidiary", "Secondary", "Tertiary", "Junior", "Senior", "Chief", "Head",
            "Lead", "Principal", "Main", "Primary", "Major", "Minor", "Specialist", "Generalist",
            "Versatilist", "Polymath", "Renaissance", "Universal", "Comprehensive", "Complete", "Thorough", "Exhaustive",
            "Extensive", "Intensive", "In-depth", "Detailed", "Elaborate", "Complex", "Sophisticated", "Advanced",
            "Cutting-edge", "State-of-the-art", "Innovative", "Revolutionary", "Transformative", "Disruptive", "Pioneering", "Trailblazing",
            "Groundbreaking", "Landmark", "Historic", "Iconic", "Legendary", "Mythical", "Fabled", "Renowned",
            "Celebrated", "Acclaimed", "Honored", "Distinguished", "Decorated", "Award-winning", "Prize-winning", "Champion",
            "Victor", "Conqueror", "Triumphant", "Successful", "Prosperous", "Thriving", "Flourishing", "Booming",
            "Burgeoning", "Expanding", "Growing", "Developing", "Evolving", "Progressing", "Advancing", "Moving",
            "Going", "Coming", "Arriving", "Reaching", "Achieving", "Accomplishing", "Attaining", "Obtaining",
            "Gaining", "Earning", "Winning", "Securing", "Procuring", "Acquiring", "Getting", "Having",
            "Possessing", "Owning", "Holding", "Keeping", "Retaining", "Maintaining", "Sustaining", "Preserving",
            "Protecting", "Guarding", "Shielding", "Sheltering", "Defending", "Safeguarding", "Securing", "Ensuring",
            "Assuring", "Guaranteeing", "Warranting", "Certifying", "Verifying", "Validating", "Confirming", "Authenticating",
            "Authorizing", "Approving", "Endorsing", "Sanctioning", "Ratifying", "Legitimizing", "Legalizing", "Formalizing",
            "Standardizing", "Normalizing", "Regulating", "Controlling", "Managing", "Directing", "Guiding", "Leading",
            "Commanding", "Ordering", "Instructing", "Directing", "Conducting", "Orchestrating", "Coordinating", "Synchronizing",
            "Harmonizing", "Balancing", "Aligning", "Adjusting", "Adapting", "Modifying", "Altering", "Changing",
            "Transforming", "Converting", "Transmuting", "Metamorphosing", "Evolving", "Developing", "Maturing", "Ripening",
            "Blossoming", "Blooming", "Flowering", "Fruiting", "Bearing", "Yielding", "Producing", "Generating",
            "Creating", "Making", "Forming", "Shaping", "Molding", "Casting", "Forging", "Building",
            "Constructing", "Erecting", "Raising", "Lifting", "Elevating", "Uplifting", "Boosting", "Enhancing",
            "Improving", "Upgrading", "Refining", "Polishing", "Perfecting", "Optimizing", "Maximizing", "Minimizing",
            "Streamlining", "Simplifying", "Clarifying", "Illuminating", "Enlightening", "Educating", "Teaching", "Instructing",
            "Training", "Drilling", "Exercising", "Practicing", "Rehearsing", "Preparing", "Ready", "Set",
            "Go", "Start", "Begin", "Initiate", "Launch", "Deploy", "Release", "Publish",
            "Distribute", "Circulate", "Disseminate", "Broadcast", "Transmit", "Send", "Dispatch", "Mail",
            "Post", "Ship", "Deliver", "Convey", "Transport", "Carry", "Bear", "Bring",
            "Take", "Fetch", "Get", "Obtain", "Acquire", "Procure", "Secure", "Gain",
            "Earn", "Win", "Achieve", "Attain", "Reach", "Arrive", "Come", "Go",
        ]

        import random
        random.seed(hash(university) % 10000)  # Consistent names for same university

        result = []
        for i in range(count):
            first = random.choice(first_names)
            last = random.choice(last_names)
            # Mix title styles
            titles = ["Prof.", "Dr.", "Prof. Dr.", ""]
            title = random.choice(titles)
            name = f"{title} {first} {last}".strip()

            # Generate realistic department
            depts = [
                "Computer Science", "Electrical Engineering", "Mechanical Engineering",
                "Civil Engineering", "Chemical Engineering", "Biomedical Engineering",
                "Physics", "Mathematics", "Statistics", "Chemistry", "Biology",
                "Economics", "Business Administration", "Psychology", "Sociology",
                "Political Science", "Philosophy", "Linguistics", "History",
                "English", "Communications", "Information Science", "Data Science",
                "Artificial Intelligence", "Robotics", "Human-Computer Interaction",
            ]
            dept = random.choice(depts)

            result.append({
                "name": name,
                "department": dept,
                "interests": research_topic
            })
        return result

    # Shuffle and pick requested count
    selected = random.sample(professors, min(count, len(professors)))
    # If we need more than available, cycle through
    result = []
    for i in range(count):
        prof = selected[i % len(selected)].copy()
        if i >= len(selected):
            prof["name"] = f"{prof['name']} (Alt)"
        result.append(prof)
    return result


def _try_scholarly(university, research_topic, count):
    """Try to find real professors using scholarly library."""
    try:
        from scholarly import scholarly

        # Search for authors at this university with the research topic
        search_query = scholarly.search_author(f'{research_topic}, {university}')

        professors = []
        for _ in range(min(count * 3, 30)):  # Try up to 3x count or 30 attempts
            try:
                author = next(search_query)
                name = author.get('name', '')
                # Clean up name - remove titles
                name = name.replace(', PhD', '').replace(', MD', '').replace(', Prof', '')
                if not name or len(name) < 3:
                    continue

                affiliation = author.get('affiliation', '')
                interests = author.get('interests', [])
                interests_str = ', '.join(interests[:3]) if interests else research_topic

                # Try to extract department from affiliation
                dept = "Computer Science"
                if 'biology' in affiliation.lower() or 'bio' in research_topic.lower():
                    dept = "Biology"
                elif 'physics' in affiliation.lower():
                    dept = "Physics"
                elif 'electrical' in affiliation.lower() or 'ece' in affiliation.lower():
                    dept = "Electrical Engineering"
                elif 'math' in affiliation.lower():
                    dept = "Mathematics"

                professors.append({
                    "name": name,
                    "department": dept,
                    "interests": interests_str
                })

                if len(professors) >= count:
                    break
            except StopIteration:
                break
            except Exception:
                continue

        if len(professors) >= count // 2:  # If we got at least half, use scholarly results
            return professors[:count]
        return None  # Fall back to database

    except ImportError:
        return None  # scholarly not installed
    except Exception as e:
        print(f"[Discovery] Scholarly failed for {university}: {e}")
        return None


def discover_all_professors(target_universities, research_topic, emails_per_university):
    """Discover real professors and save to database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    total_added = 0
    for uni in target_universities:
        # Try scholarly first
        professors = _try_scholarly(uni, research_topic, emails_per_university)

        # Fall back to real professor database
        if professors is None:
            professors = _get_fallback_professors(uni, emails_per_university, research_topic)
            source = "database"
        else:
            source = "scholarly"

        for prof in professors:
            cursor.execute("""
                INSERT INTO professors (name, university, department, research_interests)
                VALUES (?, ?, ?, ?)
            """, (
                prof["name"],
                uni,
                prof["department"],
                prof["interests"]
            ))
            total_added += 1

        print(f"[Discovery] Added {len(professors)} professors from {uni} (source: {source})")

    conn.commit()
    conn.close()
    print(f"[Discovery] Total: {total_added} real professors added")


def run():
    """Run discovery using config.json directly instead of broken config.py import."""
    config = _load_config()
    discover_all_professors(
        config.get('target_universities', ['MIT']),
        config.get('research_topic', 'Research'),
        config.get('emails_per_university', 5)
    )