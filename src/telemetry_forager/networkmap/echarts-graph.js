

data = {
  nodes: JSON.parse(context.panel.data.series[0].fields[0].values[0]),
  edges: JSON.parse(context.panel.data.series[0].fields[1].values[0]),
  categories: JSON.parse(context.panel.data.series[0].fields[2].values[0]),
};



return {
  title: {
    text: '',
    subtext: '',
    top: 'top',
    left: 'left'
  },
  tooltip: {
    trigger: 'item',
    //show: true,
    //formatter: (params) => '<div>' + 'subnet: ' + params.data.subnet + '</div>' + '<div>' + 'vnet: ' + params.data.vnet + '</div>',
    //valueFormatter: (params) => '<div>' + params.data.src_to_dest_data_size + '</div>'
  },
  animationDurationUpdate: 1000,
  animationEasingUpdate: 'quinticInOut',
  legend: [
    {
      data: ['InterVNet', 'IntraVNet', 'AzurePublic', 'ExternalPublic', 'UnknownPrivate', 'S2S', 'P2S', 'Unknown'],
      position: 'right',
      orient: 'vertical',
      right: 10,
      top: 20,
      bottom: 20
    }
  ],
  series: [
    {
      name: 'Node Name',
      type: 'graph',
      layout: 'force',
      data: data.nodes.map(n => ({
        ...n,
        tooltip: {
          formatter: function (params) {

            var subnet = ((params.data.subnet != '') ? `<div>subnet:&nbsp${params.data.subnet}</div>` : '');
            var vnet = ((params.data.vnet != '') ? `<div>vnet:&nbsp${params.data.vnet}</div>` : '');
            var src_pip_location = ((params.data.srcPIPLocation) ? `<div>src ip location:&nbsp${params.data.srcPIPLocation}</div>` : '');
            var dest_pip_location = ((params.data.destPIPLocation) ? `<div>dest ip location:&nbsp${params.data.destPIPLocation}</div>` : '');

            if (!subnet && !vnet && !src_pip_location && !dest_pip_location) {
              return ''
            }

            return subnet + vnet + src_pip_location + dest_pip_location;
          }
        }
      })),
      //links: data.edges,
      links: data.edges.map(n => ({
        ...n,
        tooltip: {
          formatter: function (params) {
            var dataSize = `${params.data.source}&nbsp&nbsp ${params.data.src_to_dest_data_size} &nbsp->&nbsp<-&nbsp ${params.data.dest_to_srct_data_size} ${params.data.target}`;
            var flowType = `<div>flow type:&nbsp ${params.data.flowType}</div>`;
            var protocol = ((params.data.protocol), `<div>protocol:&nbsp ${params.data.protocol}<div>`, '');
            var connectionType = ((params.data.connectionType), `<div>connection type:&nbsp ${params.data.connectionType}<div>`, '');
            return dataSize + flowType + protocol + connectionType
          }
        }
      })),
      categories: data.categories,//categories, //graphData.categories,

      force: {

        edgeLength: 6,
        repulsion: 20000,
        gravity: 0.1,
        friction: 1,
        layoutAnimation: true
      },


      edgeSymbol: ['none', 'arrow'],
      animation: false,
      roam: true,
      draggable: true,
      zoom: 0.2,

      symbol: 'circle',

      label: {
        show: true,
        formatter: (params) => params.data.name + '\n' + params.data.ip,
        position: 'right',
        fontSize: 12
      },

      // edgeLabel: {
      //   show: false,
      //   formatter: (params) => params.data.source + ' ' + params.data.src_to_dest_data_size + '-> <- ' + params.data.dest_to_srct_data_size + ' ' + params.datatarget + '\n' + params.data.flowType,
      //   color: '#FFF',
      //   fontSize: 11,
      //   fontStyle: 'normal'
      // },


      symbolSize: 30,

      lineStyle: {
        color: '#FFFFFF',
        width: 1,
        opacity: 1,
        curveness: 0.2
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [2, 9],

    }
  ]
};