import scriptjs from 'scriptjs';

export default function getJdEid(): Promise<{eid?: string}> {
    return new Promise(resolve => {
        const getData = () => {
            try {
                let eid;
                const riskJd = (window as any).getJdEid(res => {
                    eid = res
                    if(eid) {
                        resolve({eid})
                    }
                });
                if(!eid) {
                    resolve(riskJd || {});
                }
            } catch (e) {
                resolve({});
                console.log(e);
            }
        };
        if ((window as any).getJdEid) {
            getData();
        } else {
            scriptjs(['//gias.jd.com/js/m-tk.js'], () => {
                getData();
            });
        }
    });
}