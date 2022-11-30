"use strict";

window.addEventListener('hashchange', hashlistener)

async function hashlistener() {
    console.log(window.location.hash)

    switch(window.location.hash.split("#")[1]) {
        case "summary":
            document.getElementById("summary").style.display = "grid"
            document.getElementById("monitoring").style.display = "none"
            document.getElementById("activities").style.display = "none"
            break
        case "monitoring":
            document.getElementById("summary").style.display = "none"
            document.getElementById("monitoring").style.display = "grid"
            document.getElementById("activities").style.display = "none"
            break
        case "activities":
            document.getElementById("summary").style.display = "none"
            document.getElementById("monitoring").style.display = "none"
            document.getElementById("activities").style.display = "grid"

            if (window.location.hash.split("#").length >= 3) {
                const totals = await fetch("/api/activity/"+decodeURIComponent(window.location.hash.split("#")[2])+"/totals").then(response => response.json())

                var div = document.createElement("div")
                div.id = "div1"
                var head = document.createElement("h2")
                head.innerHTML = decodeURIComponent(window.location.hash.split("#")[2])
                document.getElementById("activities").replaceChildren(head)
                document.getElementById("activities").appendChild(div)

                var canv = document.createElement("canvas")
                canv.id = "activity_canvas"
                document.getElementById("div1").appendChild(canv)

                const records =  await fetch("/api/activity/"+decodeURIComponent(window.location.hash.split("#")[2])+"/records").then(response => response.json())

                // TODO: get these from api
                const hr_zones = [101,121,141,162,182]
                const colour_picker = ctx => {
                    if (hr_zones[4] <= ctx.p0.parsed.y) {
                        return "rgba(255,0,0,0.3)"
                    }
                    if (hr_zones[3] <= ctx.p0.parsed.y && ctx.p0.parsed.y < hr_zones[4]) {
                        return "rgba(255,165,0,0.3)"
                    }
                    if (hr_zones[2] <= ctx.p0.parsed.y && ctx.p0.parsed.y < hr_zones[3]) {
                        return "rgba(0,255,0,0.3)"
                    }
                    if (hr_zones[1] <= ctx.p0.parsed.y && ctx.p0.parsed.y < hr_zones[2]) {
                        return "rgba(0,0,255,0.3)"
                    }
                    if (hr_zones[0] <= ctx.p0.parsed.y && ctx.p0.parsed.y < hr_zones[1]) {
                        return "rgba(50,50,50,0.3)"
                    }
                    if (ctx.p0.parsed.y && ctx.p0.parsed.y < hr_zones[0]) {
                        return "rgba(150,150,150,0.3)"
                    }
                    return undefined
                }

                const data = {
                    datasets: [
                        {
                            label: "heartrate",
                            data: records.map(i => ({x: i[0], y: i[2]})),
                            radius: 0.5,
                            borderRadius: 0.01,
                            backgroundColor: "rgba(0,0,0,0.4)",
                            hoverBackgroundColor: "rgba(0,0,0,0.4)",
                            segment: {
                                borderColor: ctx => "rgba(0,0,0,0.1)",
                                backgroundColor: ctx => colour_picker(ctx)
                            },
                            fill: true,
                            spanGaps: true
                        }
                    ]
                }
            
                const config = {
                    type: 'line',
                    data: data,
                    options: {
                        scales: {
                          x: {
                            type: 'time',
                            position: 'bottom',
                            },
                          y: {
                            type: 'linear',
                            position: 'left',
                            beginAtZero: true
                          }
                        }
                    }
                }
            
                const ctx = document.getElementById("activity_canvas")
                return new Chart(ctx, config);
            }
            else {
                document.getElementById("activities").replaceChildren("Activity not found")
            }



            break
        default:
            break            
    }
}


async function test() {
    var canv = document.createElement("canvas")
    canv.id = "canvas"

    document.getElementById("graph").appendChild(canv)

    var raw_data = await fetch("/api/summary?total_distance").then(response => response.json())

    const data = {
        datasets: [
            {
                label: "total distance",
                data: raw_data.map(i => ({x: i[0], y: i[1]}))
            }
        ]
    }

    const config = {
        type: 'scatter',
        data: data,
        options: {
            scales: {
              x: {
                type: 'time',
                position: 'bottom',
                }
            }
        }
    }

    const ctx = document.getElementById("canvas")
    return new Chart(ctx, config);
}

var chart_graph = test()

async function update_chart(label, column) {
    chart_graph = await chart_graph

    if (this.checked) {
        var raw_data = await fetch("/api/summary?"+column).then(response => response.json())
        chart_graph.data.datasets = [
            {label: label, data: raw_data.map(i => ({x: i[0], y: i[1]}))}
        ]
        chart_graph.update()
    }
}

async function update_chart_grouping() {
    chart_graph = await chart_graph

    if (this.value == "none") {
        document.getElementsByName("scatter").forEach(n => {
            n.style.display = "inline"
            document.querySelector("label[for="+n.id+"]").style.display = "inline"
        })

        var raw_data = await fetch("/api/summary?total_distance").then(response => response.json())

        chart_graph.config.type = 'scatter'
        chart_graph.data.datasets = [
            {
                label: "total distance",
                data: raw_data.map(i => ({x: i[0], y: i[1]}))
            }
        ]
        chart_graph.type = 'scatter'
        chart_graph.options.scales = {
            x: {
              type: 'time',
              position: 'bottom',
            }
          }
        chart_graph.update()

        document.getElementById("total_distance").checked = true
    }
    else {
        document.getElementsByName("scatter").forEach(n => {
            n.style.display = "none"
            document.querySelector("label[for="+n.id+"]").style.display = "none"
        })


        var raw_data = await fetch("/api/summary/totals?group_by="+this.value).then(response => response.json())

        chart_graph.config.type = 'bar'

        chart_graph.options = {
            scales: {
                x: {
                    type: 'time',
                    position: 'bottom'
                },
                y_activities: {
                    type: 'linear',
                    position: 'left',
                },
                y_dist: {
                    type: 'linear',
                    position: 'left',
                },
                y_time: {
                    type: 'linear',
                    position: 'left',
                },
            }
        }
        chart_graph.data = {
            labels: raw_data.map(i => i[0]),
            datasets: [
                {
                    label: "total activities",
                    data: raw_data.map(i => i[1]),
                    yAxisID: "y_activities"
                },
                {
                    label: "total distance",
                    data: raw_data.map(i => i[2]),
                    yAxisID: "y_dist"
                },
                {
                    label: "total time",
                    data: raw_data.map(i => i[3]),
                    yAxisID: "y_time"
                }
            ]
        }
        
        chart_graph.update()
    }
}


document.getElementById("group_by").value = "none"
document.getElementById("total_distance").checked = true

document.getElementById("group_by").addEventListener("change", function() {update_chart_grouping.bind(this)()})

document.getElementsByName("scatter").forEach(n => n.addEventListener("change", function() {update_chart.bind(this)(n.id, n.id)}))

async function get_records() {
    const data = await fetch("/api/summary/totals?group_by=all").then(response => response.json())

    const hours = Math.floor(data[0][2]/3600)
    const mins = Math.floor((data[0][2]-hours*3600)/60)
    const secs = Math.round(data[0][2]%60)
    document.getElementById("total_time").innerHTML = hours+":"+mins+":"+secs
    document.getElementById("total_distance").innerHTML = (data[0][1]/1000).toFixed(2)+"km"
    document.getElementById("total_activities").innerHTML = data[0][0]
}

get_records()


async function get_activities() {
    const data = await fetch("/api/summary").then(response => response.json())

    data.reverse().forEach(x => {
        var li = document.createElement("li")
        var a = document.createElement("a")
        a.innerHTML = x
        a.href="#activities#"+x
        li.appendChild(a)
        document.querySelector("#navbar ul").appendChild(li)
    })

}

get_activities()