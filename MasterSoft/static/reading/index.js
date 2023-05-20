// Define an object with options for formatting the date and time
let options = {
  year: 'numeric',
  month: 'numeric',
  day: 'numeric',
  hourCycle: 'h23',
  hour: 'numeric',
  minute: 'numeric',
  second: 'numeric'
};

// Define a function that takes an array of readings and an index as parameters
function html_data_binding(readings, index) {
  // Use jQuery to update the HTML elements with the corresponding values from the readings array
  $(`#id-${index}`).html(`${readings[index].id}`);
  $(`#order-num-${index}`).html(`${readings[index].order_num}`);
  $(`#xmter-${index}`).html(`${readings[index].trans_id}`);
  $(`#rtd-1-${index}`).html(`${readings[index].rtd_1} Ω`);
  $(`#temp-1-${index}`).html(`${readings[index].temp_1.toFixed(3)} °C`);
  $(`#rtd-2-${index}`).html(`${readings[index].rtd_2} Ω`);
  $(`#temp-2-${index}`).html(`${readings[index].temp_2.toFixed(3)} °C`);
  $(`#requestor-id-${index}`).html(`${readings[index].requestor_id}`);
  // Use the options object to format the date and time of the reading
  $(`#at-${index}`).html(`${(new Date(readings[index].created_at)).toLocaleString("en-US", options)}`);
};
function html_header_binding(nodes) {
  let master_node;
  if (nodes.master_list.length >= 1) {
    master_node = nodes.master_list.find(node => node.power == 0);
  };
  $("#base-master").html(`${master_node.hostname}`);
  $("#online-xmter").html(`${nodes.transmitter_list.length}/19`);
  $("#online-master").html(`${nodes.master_list.length}/5`);
  $("#web-server").html(`${nodes.interface_list.length}/2`);
  $("#data-server").html(`${nodes.data_server_list.length}/3`);
  $("#main-pc").html(`${nodes.maintenance_pc_list.length}/2`);
}

// Define a function that gets data from the server
function get_data_from_server() {
  // Send an AJAX GET request to the Flask view function
  $.ajax({
    type: "GET",
    url: "http://127.0.0.1:60305/internal-reading-list",
    success: function(data) {
      $("#power-level").html(`Power level: ${data.node["power"]}`);
      // Use a loop to call the html_data_binding function for each reading in the array
      for (let i = 0; i < data.readings.length; i++) {
        html_data_binding(data.readings, i);
      }
      html_header_binding(data.nodes);
    }
  });
}

// Set the interval in milliseconds
const interval = 10000;

// Call the get_data_from_server function once
get_data_from_server();

// Call the get_data_from_server function every interval milliseconds
setInterval(get_data_from_server, interval);