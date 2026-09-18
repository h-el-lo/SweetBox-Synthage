void loop() {
  // ============  READ THROUGH ALL POTS MINUS PITCH AND MOD WHEELS  =====================
  for (int i = 0; i < N_POTS; i++) {
    potReading[i] = analogRead(potPin[i]);
    potState[i] = potReading[i];
    midiState[i] = map(potState[i], 0, 1023, ccMin[i], ccMax[i]);

    int potVar = abs(potState[i] - potPState[i]);

    if (potVar > potThreshold) {
      pPotTime[i] = millis();
    }

    potTimer[i] = millis() - pPotTime[i];

    if (potTimer[i] < POT_TIMEOUT) {
      if (midiState[i] != midiPState[i]) {
        uControlChange(potChannel[i], potCC[i], midiState[i]);
        bControlChange(potChannel[i], potCC[i], midiState[i]);
        midiPState[i] = midiState[i];
      }
      potPState[i] = potState[i];
    }
  }
}