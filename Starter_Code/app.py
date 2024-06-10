# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# 2. Create an app, being sure to pass __name__
app = Flask(__name__)

#################################################
# Database Setup
#################################################

# Create an engine connected to the database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
table_references = {table_name: Base.classes[table_name] for table_name in Base.metadata.tables.keys()}
Measurement = table_references['measurement']
Station = table_references['station']

# Create our session (link) from Python to the DB
session = Session(engine)


#################################################
# Flask Setup
#################################################
#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    return (
        f"Welcome to the first climate analysis API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    recent_date = session.query(func.max(Measurement.date)).scalar()
    recent_date = datetime.strptime(recent_date, '%Y-%m-%d')

    # Perform a query to retrieve the data and precipitation scores within the last 12 months
    prcp_results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= func.date(recent_date, '-1 year')).\
        all()

    # Convert the query results to a dictionary with date as the key and prcp as the value
    prcp_dict = {result.date: result.prcp for result in prcp_results}

    # Return the data as JSON
    return jsonify(prcp_dict)

session.close()

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    stations = session.query(Station.station).all()
    all_stations = [station[0] for station in stations]
    

    return jsonify(all_stations)

session.close()

@app.route("/api/v1.0/tobs")
def temperature():

    session = Session(engine)

    recent_date_str = session.query(func.max(Measurement.date)).scalar()
    recent_date = datetime.strptime(recent_date_str, '%Y-%m-%d')
    one_year_ago = recent_date - timedelta(days=365)


    station_id = 'USC00519281'

    tobs_results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == station_id).\
        filter(Measurement.date >= one_year_ago).all()
    
    tobs_list = [{"Date": result.date, "Temperature": result.tobs} for result in tobs_results]

    return jsonify(tobs_list)

session.close()

@app.route("/api/v1.0/tobs/<start>", defaults={'end': ''})
@app.route("/api/v1.0/tobs/<start>/<end>")
def period_analysis(start, end):
    
    session = Session(engine)

    start_date = datetime.strptime(start, '%Y-%m-%d')
    
    if end == "":
        end_date_str = session.query(func.max(Measurement.date)).scalar()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        end_date = datetime.strptime(end, '%Y-%m-%d')

    tobs_results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= start_date).\
        filter(Measurement.date <= end_date).all()

    temperature_stats = session.query(
        func.min(Measurement.tobs).label('min_temp'),
        func.max(Measurement.tobs).label('max_temp'),
        func.avg(Measurement.tobs).label('avg_temp')
        ).filter(Measurement.date >= start_date).\
          filter(Measurement.date <= end_date).one()

    min_temp = temperature_stats.min_temp
    max_temp = temperature_stats.max_temp
    avg_temp = temperature_stats.avg_temp


    tobs_dict = {
            "start_date": start,
            "end_date": end if end else end_date_str,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "avg_temp": avg_temp,
            "observations": {result.date: result.tobs for result in tobs_results}
        }

    return jsonify(tobs_dict)
    
session.close()


if __name__ == "__main__":
    app.run(debug=True)