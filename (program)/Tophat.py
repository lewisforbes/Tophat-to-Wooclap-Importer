import csv
import re
import utils

class Tophat:
    def __init__(self, th_dir, show_warnings=True):
        self.show_warnings = show_warnings
        fnames = utils.dir_fnames(th_dir)

        self.th_headers = []
        self.lines = []
        self.missing = [] 
        self.parse(th_dir+fnames[0])

    def parse(self, fname):
        def str_to_bool(str):
            if str=="TRUE":
                return True
            if str=="FALSE" or str=="":
                return False
            utils.exception("Not a boolean. String was {}".format(str))
            
        f = open(fname, 'r')
        first = True

        for l in csv.reader(f, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True):
            if first:
                self.th_headers = l
                first = False
                continue
            
            self.lines.append(Line(l, l[2]+"\n"+l[3], str_to_bool(l[4]), str_to_bool(l[5])))

        f.close()

    def mk_img_tol_miss(self, wc_qs, outname="img_tol_miss.csv"):
        def order_output(output):
            # changes None output of utils.get_value to 0 for ordering
            def _get_value(tag, t):
                r = utils.get_value(tag, t)
                if r:
                    return r 
                else:
                    return 0
            output.sort(key=lambda l: _get_value(l[0], "Q")) 
            output.sort(key=lambda l: _get_value(l[0], "S")) 
            output.sort(key=lambda l: _get_value(l[0], "F")) 

        self.mk_missing(wc_qs)
        to_write = []
        for l in self.lines:
            img_tol_miss = [l.has_img, l.has_tol, l.missing]
            if True in img_tol_miss:
                tag = utils.get_tag(l.wc_q)
                if tag==None:
                    continue
                to_write.append([tag] + ["" if b==False else b for b in img_tol_miss])
                
        order_output(to_write)
        headers = ["tag", "has image", "has tolerance", "missing"]
        contents = [headers] + to_write
        utils.write_csv(contents, outname)

    def mk_missing(self, wc):
        wc_qs = wc.get_all_qs()
        self.missing = []
        for th_line in self.lines:
            found=False
            for wc_q in wc_qs:
                if th_line.tag == utils.get_tag(wc_q):
                    found=True
                    break
            if not found:
                self.missing.append(th_line.tag)
        
        for tag, nc in wc.names_counts.items():
            f_i = utils.get_value(tag, "F")
            sf_i=None
            if "S" in tag:
                sf_i=utils.get_value(tag, "S")
            f = wc.get_folder_i(f_i, sf_i)
            if len(f.questions)>nc[1]:
                if self.show_warnings:
                    utils.warning("{} has {} questions - you said there were {}!".format(tag, len(f.questions), nc[1]))
                continue

            if len(f.questions)==nc[1]:
                continue
            else:
                for q_i in range(1, nc[1]+1):
                    try:
                        f.get_question(q_i)
                        # q_i exists
                    except:
                        # q_i does not exist
                        full_tag = "{}Q{}".format(tag, q_i)
                        if not (full_tag in self.missing):
                            self.missing.append(full_tag)
                            self.lines.append(Line(None, full_tag, None, None))


        for l in self.lines:
            l.missing = l.tag in self.missing

    def is_line(self, tag):
        return tag in [l.tag for l in self.lines]
    

class Line:
    def __init__(self, full, th_q, has_img, has_tol):
        self.full = full
        self.wc_q = self.q_converter(th_q)
        self.has_img = has_img
        self.has_tol = has_tol
        self.missing = None
        self.tag = utils.get_tag(th_q)

    def q_converter(self, th_q):
        wc_q = re.sub("<[^>]*>", "", th_q)
        if "[math]" in wc_q:
            wc_q = wc_q.replace("[math]", "$").replace("[/math]", "$")
        return wc_q
