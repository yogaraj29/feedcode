const addIOBtn = document.getElementById('addIOBtn');
const ioContainer = document.getElementById('ioContainer');

let ioCount = 1;

addIOBtn.addEventListener('click', () => {
    const ioField = `
        <div class="d-flex row mb-3">
            <div class="col-md-5">
                <textarea class="form-control" id="in${ioCount}" name="in${ioCount}" placeholder="Input ${ioCount}" rows="2" required></textarea>
            </div>
            <div class="col-md-5">
                <textarea class="form-control" id="op${ioCount}" name="op${ioCount}" placeholder="Output ${ioCount}" rows="2" required></textarea>
            </div>
            <div class="col-md-2 text-end">
                <button type="button" class="btn btn-danger btn-sm" onclick="removeIOField(this)">Remove</button>
            </div>
        </div>
    `;
    ioContainer.insertAdjacentHTML('beforeend', ioField);
    ioCount++;
});

function removeIOField(btn) {
    btn.closest('.row').remove();
    ioCount--;
}

function submitQuestion() {
    const topic = document.getElementById('topic').value;
    const description = document.getElementById('description').value;
    const constraints = document.getElementById('constraints').value;

    const ioFields = document.querySelectorAll('#ioContainer .row');
    const inputs = [];
    const outputs = [];

    ioFields.forEach((field) => {
        const input = field.querySelector('textarea:nth-of-type(1)').value;
        const output = field.querySelector('textarea:nth-of-type(2)').value;
        inputs.push(input);
        outputs.push(output);
    });

    const tableBody = document.getElementById('questionsTableBody');

    const newRow = tableBody.insertRow();
    const cell1 = newRow.insertCell(0);
    const cell2 = newRow.insertCell(1);
    const cell3 = newRow.insertCell(2);
    const cell4 = newRow.insertCell(3);

    cell1.innerHTML = topic;
    cell2.innerHTML = description;
    cell3.innerHTML = constraints;
    cell4.innerHTML = `
        <ul>
            ${inputs.map(input => `<li>${input}</li>`).join('')}
        </ul>
        <ul>
            ${outputs.map(output => `<li>${output}</li>`).join('')}
        </ul>
    `;

    const questionModal = document.getElementById('questionModal');
    const bootstrapModal = bootstrap.Modal.getInstance(questionModal);
    bootstrapModal.hide();
    questionForm.reset();
    ioContainer.innerHTML = '';
    ioCount = 1;
}