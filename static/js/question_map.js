document.addEventListener('DOMContentLoaded', function () {
    // Parse the question data from the DOM
    var questionData = JSON.parse(document.getElementById('question-nodes-data').textContent);

    // Get the dimensions for the SVG
    var width = document.getElementById('chart').clientWidth;
    var height = 800; // İhtiyacınıza göre ayarlayabilirsiniz

    // Create the SVG element with zoom and pan functionality
    var svg = d3.select("#chart")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    // Create a group to hold all elements
    var g = svg.append("g");

    // Define the arrow markers for links
    var defs = svg.append("defs");

    defs.append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "-0 -5 10 10")
        .attr("refX", 25)
        .attr("refY", 0)
        .attr("orient", "auto")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#999");

    // Define the zoom behavior and assign it to a variable
    var zoom = d3.zoom()
        .scaleExtent([0.05, 5]) // Allow zooming out more to see all nodes
        .on("zoom", function (event) {
            g.attr("transform", event.transform);
            updateNodeVisibility(event.transform.k);
        });

    // Apply zoom behavior to the svg
    svg.call(zoom);

    // Initialize the simulation
    var simulation = d3.forceSimulation(questionData.nodes)
        .force("link", d3.forceLink(questionData.links)
            .id(function (d) { return d.id; })
            .distance(150)
        )
        .force("charge", d3.forceManyBody()
            .strength(-200)
        )
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide()
            .radius(function (d) { return d.size * 1.5; })
        )
        .on('end', function() {
            if (focusQuestionId) {
                var targetNode = questionData.nodes.find(node => node.question_id.toString() === focusQuestionId);
                if (targetNode) {
                    // Haritayı hedef düğüme yakınlaştırın
                    zoomToNode(targetNode);
                }
            }
        });

    // Create links
    var link = g.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(questionData.links)
        .enter().append("line")
        .attr("stroke-width", 2)
        .attr("stroke", "#999")
        .attr("marker-end", "url(#arrowhead)");

    // Create nodes
    var node = g.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(questionData.nodes)
        .enter().append("circle")
        .attr("r", function (d) { return d.size; })
        .attr("fill", function (d) {
            if (d.users.length > 1) {
                return "#A9A9A9"; // Ortak sorular için gri renk
            } else {
                return d.color; // Kullanıcıya özel renk
            }
        })
        .on("click", function (event, d) {
            window.location.href = "/question/" + d.question_id + "/";
        })
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
        );

    // Create labels
    var label = g.append("g")
        .attr("class", "labels")
        .selectAll("text")
        .data(questionData.nodes)
        .enter().append("text")
        .attr("dy", -10)
        .attr("text-anchor", "middle")
        .text(function (d) { return d.label; })
        .style("font-size", function (d) {
            // Kullanıcı sayısına göre temel font boyutu
            return (12 + (d.users.length * 2)) + "px";
        });

    // Start the simulation
    simulation
        .on("tick", ticked);

    // Ticking function to update positions
    function ticked() {
        link
            .attr("x1", function (d) { return d.source.x; })
            .attr("y1", function (d) { return d.source.y; })
            .attr("x2", function (d) { return d.target.x; })
            .attr("y2", function (d) { return d.target.y; });

        node
            .attr("cx", function (d) { return d.x; })
            .attr("cy", function (d) { return d.y; });

        label
            .attr("x", function (d) { return d.x; })
            .attr("y", function (d) { return d.y - d.size - 5; }); // Etiketi düğümün üstüne yerleştirin
    }

    // Dragging functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        // Düğümlerin serbest kalmasını istiyorsanız aşağıdaki satırları yorumdan çıkarın
        // d.fx = null;
        // d.fy = null;
    }

    // Function to update node visibility based on zoom level
    function updateNodeVisibility(zoomLevel) {
        node.each(function(d) {
            // Kullanıcı sayısına göre düğüm opaklığını ayarlayın
            var minOpacity = 0.8;
            var maxOpacity = 0.9;
            var userCountFactor = (d.users.length - 1) / (questionData.maxUserCount - 1) || 0;
            var opacity = minOpacity + (maxOpacity - minOpacity) * userCountFactor;
    
            // Zoom seviyesine göre opaklığı ayarlayın
            if (zoomLevel < 0.5) {
                opacity = opacity * zoomLevel * 2; // Daha az önemli düğümleri soluklaştırın
            }
            d.opacity = opacity; // Hesaplanan opaklığı veriye kaydedin
    
            // Düğümün opaklığını uygulayın
            d3.select(this).style("opacity", d.opacity);
        });
    
        label.each(function(d) {
            // Etiketler düğümlerle aynı opaklığa sahip olsun
            d3.select(this).style("opacity", d.opacity);
        });
    
        label.style("font-size", function(d) {
            // Zoom seviyesi ve kullanıcı sayısına göre font boyutunu ayarlayın
            var baseSize = 12 + (d.users.length * 2);
            return baseSize * zoomLevel + "px";
        });
    }

    // Compute the maximum number of users for any question
    questionData.maxUserCount = d3.max(questionData.nodes, function(d) { return d.users.length; }) || 1;

    // Initialize node visibility
    updateNodeVisibility(1);

    // Seçili kullanıcıları tutmak için bir dizi
    var selectedUsers = [];

    // Kullanıcı arama sonuçlarına tıklandığında
    document.getElementById('user-search-results').addEventListener('click', function (event) {
        if (event.target && event.target.matches('.user-search-item')) {
            var userId = event.target.dataset.userId;
            var username = event.target.textContent;

            // Kullanıcı zaten seçiliyse eklemeyin
            if (!selectedUsers.includes(userId)) {
                selectedUsers.push(userId);
                addUserToSelectedList(userId, username);
            }

            document.getElementById('user-search-input').value = '';
            this.style.display = 'none';
        }
    });

    // Seçili kullanıcılar listesine kullanıcı ekleme fonksiyonu
    function addUserToSelectedList(userId, username) {
        var userList = document.getElementById('selected-users-list');
        var li = document.createElement('li');
        li.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
        li.textContent = username;
        li.dataset.userId = userId;

        var removeBtn = document.createElement('button');
        removeBtn.classList.add('btn', 'btn-sm', 'btn-danger');
        removeBtn.textContent = 'Kaldır';
        removeBtn.addEventListener('click', function () {
            // Kullanıcıyı listeden ve seçili kullanıcılardan kaldır
            selectedUsers = selectedUsers.filter(function (id) {
                return id !== userId;
            });
            userList.removeChild(li);
        });

        li.appendChild(removeBtn);
        userList.appendChild(li);
    }

    // "Filtrele" butonuna tıklandığında
    document.getElementById('btn-filter-users').addEventListener('click', function () {
        if (selectedUsers.length > 0) {
            var params = selectedUsers.map(function(id) {
                return 'user_id=' + id;
            }).join('&');
            fetch('/map-data/?' + params)
                .then(response => response.json())
                .then(data => {
                    updateGraph(data);
                });
        }
    });

    // "Ben" ve "Tümü" butonlarına tıklandığında seçili kullanıcıları temizleyin
    document.getElementById('btn-me').addEventListener('click', function () {
        // Seçili kullanıcıları temizleyin
        selectedUsers = [];
        document.getElementById('selected-users-list').innerHTML = '';

        fetch('/map-data/?filter=me')
            .then(response => response.json())
            .then(data => {
                updateGraph(data);
            });
    });

    document.getElementById('btn-all').addEventListener('click', function () {
        // Seçili kullanıcıları temizleyin
        selectedUsers = [];
        document.getElementById('selected-users-list').innerHTML = '';

        fetch('/map-data/')
            .then(response => response.json())
            .then(data => {
                updateGraph(data);
            });
    });

    // User search functionality
    document.getElementById('user-search-input').addEventListener('input', function () {
        var query = this.value;
        if (query.length > 0) {
            fetch('/user-search/?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    var resultsDiv = document.getElementById('user-search-results');
                    resultsDiv.innerHTML = '';
                    data.results.forEach(function (user) {
                        var div = document.createElement('div');
                        div.classList.add('user-search-item');
                        div.textContent = user.username;
                        div.dataset.userId = user.id;
                        resultsDiv.appendChild(div);
                    });
                    resultsDiv.style.display = 'block';
                });
        } else {
            document.getElementById('user-search-results').style.display = 'none';
        }
    });

    // Hide user search results when clicking outside
    document.addEventListener('click', function (event) {
        if (!event.target.closest('#user-search-input') && !event.target.closest('#user-search-results')) {
            document.getElementById('user-search-results').style.display = 'none';
        }
    });

    // Function to zoom to a specific node
    function zoomToNode(node) {
        var scale = 1.5; // Yakınlaştırma ölçeği
        var x = -node.x * scale + width / 2;
        var y = -node.y * scale + height / 2;
        svg.transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
    }

    // Function to update the graph with new data
    function updateGraph(newData) {
        // Stop the simulation
        simulation.stop();

        // Remove existing elements
        link.remove();
        node.remove();
        label.remove();

        // Update questionData
        questionData = newData;

        // Recalculate maxUserCount
        questionData.maxUserCount = d3.max(questionData.nodes, function (d) { return d.users.length; }) || 1;

        // Recreate links
        link = g.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(questionData.links)
            .enter().append("line")
            .attr("stroke-width", 2)
            .attr("stroke", "#999")
            .attr("marker-end", "url(#arrowhead)");

        // Recreate nodes
        node = g.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(questionData.nodes)
            .enter().append("circle")
            .attr("r", function (d) { return d.size; })
            .attr("fill", function (d) {
                if (d.users.length > 1) {
                    return "#A9A9A9";
                } else {
                    return d.color;
                }
            })
            .on("click", function (event, d) {
                window.location.href = "/question/" + d.question_id + "/";
            })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended)
            );

        // Recreate labels
        label = g.append("g")
            .attr("class", "labels")
            .selectAll("text")
            .data(questionData.nodes)
            .enter().append("text")
            .attr("dy", -10)
            .attr("text-anchor", "middle")
            .text(function (d) { return d.label; })
            .style("font-size", function (d) {
                return (12 + (d.users.length * 2)) + "px";
            });

        // Restart the simulation with new data
        simulation.nodes(questionData.nodes);
        simulation.force("link").links(questionData.links);
        simulation.alpha(1).restart();

        // Initialize node visibility
        updateNodeVisibility(1);
    }

    // User search functionality
    document.getElementById('user-search-input').addEventListener('input', function () {
        var query = this.value;
        if (query.length > 0) {
            fetch('/user-search/?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    var resultsDiv = document.getElementById('user-search-results');
                    resultsDiv.innerHTML = '';
                    data.results.forEach(function (user) {
                        var div = document.createElement('div');
                        div.classList.add('user-search-item');
                        div.textContent = user.username;
                        div.dataset.userId = user.id;
                        resultsDiv.appendChild(div);
                    });
                    resultsDiv.style.display = 'block';
                });
        } else {
            document.getElementById('user-search-results').style.display = 'none';
        }
    });

    // Hide user search results when clicking outside
    document.addEventListener('click', function (event) {
        if (!event.target.closest('#user-search-input') && !event.target.closest('#user-search-results')) {
            document.getElementById('user-search-results').style.display = 'none';
        }
    });

    // Function to zoom to a specific node
    function zoomToNode(node) {
        var scale = 1.5; // Yakınlaştırma ölçeği
        var x = -node.x * scale + width / 2;
        var y = -node.y * scale + height / 2;
        svg.transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
    }
});
