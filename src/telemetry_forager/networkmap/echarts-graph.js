graphData = {
    data: [
      {
        name: 'CNF',
        id: 'CNF',
        category: 1,
        ip: '12.20.11.23',
        name: 'Azure Monitor',
        subnet: "some text",
        vnet: '123',
      },
      {
        name: 'SCPC',
        id: 'SCPC',
        category: 2,
        ip: '12.20.11.23',
        name: 'Azure Monitor',
        subnet: "some text",
        vnet: '123'
      },
      {
        name: 'NRF',
        id: 'NRF',
        category: 3,
        ip: '12.20.11.23',
        name: 'Azure Monitor',
        subnet: "some text",
        vnet: '123'
      },
      {
        name: 'SCPI',
        id: 'SCPI',
        ip: '12.20.11.23',
        name: 'Azure Monitor',
        subnet: "some text",
        vnet: '123'
      },
      {
        name: 'SCPE',
        id: 'SCPE',
        category: 5,
        ip: '12.20.11.23',
        name: 'Azure Monitor',
        subnet: "some text",
        vnet: '123'
      },
      {
        name: 'NMS',
        d: 'NMS',
        category: 6,
        ip: '12.20.11.23',
        name: 'Azure Monitor',
        subnet: "some text",
        vnet: '123'
      }
    ],
    link: [
      {
        source: 'CNF',
        target: 'SCPC',
        src_to_dest_data_size: '10 KB',
        dest_to_srct_data_size: '22 KB',
        flowType: 'Azure Public PaaS'
      },
      {
        source: 'SCPC',
        target: 'NRF',
        src_to_dest_data_size: '10 KB',
        dest_to_srct_data_size: '22 KB',
        flowType: 'Azure Public PaaS'
      },
      {
        source: 'SCPC',
        target: 'SCPI',
        src_to_dest_data_size: '10 KB',
        dest_to_srct_data_size: '22 KB',
        flowType: 'Azure Public PaaS'
      },
      {
        source: 'SCPC',
        target: 'SCPE',
        src_to_dest_data_size: '10 KB',
        dest_to_srct_data_size: '22 KB',
        flowType: 'Azure Public PaaS'
      },
      {
        source: 'SCPC',
        target: 'NMS',
        src_to_dest_data_size: '10 KB',
        dest_to_srct_data_size: '22 KB',
        flowType: 'Azure Public PaaS'
      }
    ],
    categories: [
      {
        name: 'SCPC'
      },
      {
        name: 'CNF'
      },
      {
        name: 'SCPE'
      },
      {
        name: 'SCPI'
      },
      {
        name: 'NRF'
      },
      {
        name: 'NMS'
      }
    ]
  };
  
  
  data = {
    nodes: JSON.parse(context.panel.data.series[0].fields[0].values[0]),
    edges: JSON.parse(context.panel.data.series[0].fields[1].values[0]),
    categories: JSON.parse(context.panel.data.series[0].fields[2].values[0]),
  };
  
  console.log(data.nodes)
  
  
  // nodes = tempNodes.map((n, i) => ({
  //   name: n.name,
  //   id: n.id,
  //   category: n.category,
  //   ip: n.ip,
  //   name: n.name,
  //   subnet: n.subnet,
  //   vnet: n.vnet
  // }));
  
  
  
  // context.panel.data.series.map((s) => {
  //   if (s.refId === "A") {
  //     nodes = context.panel.data.series[0].fields[0].values[0];
  //     edges = context.panel.data.series[0].fields[1].values[0];
  
  //     //nodes = JSON.parse(s.fields.find((f) => f === "nodes"));
  //     //edges = s.fields.find((f) => f.name === "edges").values;
  //     //categories = s.fields.find((f) => f.name === "categories").values;
  
  //   }
  // });
  
  
  
  
  return {
    title: {
      text: '',
      subtext: '',
      top: 'top',
      left: 'left'
    },
    tooltip: {
      show: true,
      formatter: (params) => '<div>' + 'subnet: ' + params.data.subnet + '</div>' + '<div>' + 'vnet: ' + params.data.vnet + '</div>',
      //valueFormatter: (params) => '<div>' + params.data.src_to_dest_data_size + '</div>'
    },
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quinticInOut',
    // legend: [
    //   {
    //     data: ['SCPC', 'CNF', 'SCPE', 'SCPI', 'NRF', 'NMS'],
    //     position: 'right',
    //     orient: 'vertical',
    //     right: 10,
    //     top: 20,
    //     bottom: 20
    //   }
    // ],
    series: [
      {
        name: 'Node Name',
        type: 'graph',
        layout: 'force',
        data: data.nodes.map(n => ({
          ...n,
          // tooltip: {
          //   formatter: (params) => '<div>' + 'subnet: ' + params.data.subnet + '</div>' + '<div>' + 'vnet: ' + params.data.vnet + '</div>'
          // }
        })),
        links: data.edges,
        categories: data.categories,//categories, //graphData.categories,
        // force: {
        //   repulsion: 100,
        //   edgeLength: 5,
        //   gravity: 0.1
        // },
        force: {
          //initLayout: 'circular',
  
          replulsion: 100,
          // edgeLength: [50, 100]
        },
  
        edgeSymbol: ['none', 'arrow'],
        animation: false,
        roam: true,
        draggable: true,
        zoom: 5,
  
        symbol: 'circle',
  
        label: {
          show: true,
          formatter: (params) => params.data.name + '\n' + params.data.ip,
          position: 'right',
          fontSize: 12
        },
  
        edgeLabel: {
          show: false,
          formatter: (params) => params.data.src_to_dest_data_size + '-> <- ' + params.data.dest_to_srct_data_size + '\n' + params.data.flowType,
          color: '#FFF',
          fontSize: 11,
          fontStyle: 'normal'
        },
  
        symbolSize: 10,
  
        lineStyle: {
          color: '#FFFFFF',
          width: 1,
          opacity: 1,
          curveness: 0.2
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 2
          }
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [2, 8],
  
      }
    ]
  };