import acm_report
import acm_report.views
from acm_report import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001, debug=True)
