function similarityInput(rule, name) {
  var $container = rule.$el.find('.rule-value-container')
  $container.on('input', '[name=' + name + '_range]', function () {
    var threshold = rule.$el.find('.rule-value-container [name$=_range]').val()
    rule.$el.find('.rule-value-container [name$=_rangevalue]').text(threshold)
  })

  return `
    <input name="${name}_text" type="text" style="width:500px;">
    <br>
    <input name="${name}_range" type="range" class="form-range" min="-1" max="1" step="0.01" style="width:400px;">
    <span name="${name}_rangevalue" style="margin-left: 35px;">0</span>`
}

// Pass value and threshold as string data using JSON serialization
function similarityValueGetter(rule) {
  var text = rule.$el.find('.rule-value-container [name$=_text]').val()
  var threshold = rule.$el.find('.rule-value-container [name$=_range]').val()
  return JSON.stringify({ text: text, threshold: threshold })
}

function similarityValueSetter(rule, value) {
  value = JSON.parse(value)
  console.log(value)
  rule.$el.find('.rule-value-container [name$=_text]').val(value['text']).trigger('change')
  rule.$el.find('.rule-value-container [name$=_range]').val(value['threshold']).trigger('change')
  rule.$el.find('.rule-value-container [name$=_rangevalue]').text(value['threshold'])
}

var customFilters = {
  Similarity: {
    input: similarityInput,
    valueGetter: similarityValueGetter,
    valueSetter: similarityValueSetter,
  },
}

function hydrateCustomFilters(filters) {
  for (var i = 0; i < filters.length; i++) {
    var id = filters[i]['id']
    if (id in customFilters) {
      filters[i] = { ...filters[i], ...customFilters[id] }
    }
  }
  return filters
}
